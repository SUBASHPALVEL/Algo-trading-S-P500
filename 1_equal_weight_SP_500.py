"""
author SubashPalvel

The S&P 500 is the world's most popular stock market index.

The goal of this section is to create a Python script that will accept the value of your portfolio and tell you how many shares of each S&P 500 constituent you should purchase to get an equal-weight version of the index fund.
"""

# 1 import statements

import numpy as np 
import pandas as pd 
import requests 
import xlsxwriter 
import math 

# 2 import S&P_500 file

stocks = pd.read_csv('S&P_500.csv')

# 3 Acquiring an API Token

IEX_CLOUD_API_TOKEN = 'Tpk_059b97af715d417d9f49f50b51b1c448' 

# 4 Adding Our Stocks Data to a Pandas DataFrame using Batch API Call

my_columns = ['Ticker', 'Price','Market Capitalization', 'Number Of Shares to Buy']

"""

Batch API calls are one of the easiest ways to improve the performance of your code.

This is because HTTP requests are typically one of the slowest components of a script.

In this section, we'll split our list of stocks into groups of 100 and then make a batch API call for each group.

"""

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))
                  # print(symbol_strings[i])

final_dataframe = pd.DataFrame(columns = my_columns)

for symbol_string in symbol_strings:
                  # print(symbol_strings)
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(
                                        pd.Series([symbol, 
                                                   data[symbol]['quote']['latestPrice'], 
                                                   data[symbol]['quote']['marketCap'], 
                                                   'N/A'], 
                                                  index = my_columns), 
                                        ignore_index = True)
        
# 5 Calculating the Number of Shares to Buy

portfolio_size = input("Enter the value of your portfolio:")
try:
    val = float(portfolio_size)
except ValueError:
    print("That's not a number! \n Try again:")
    portfolio_size = input("Enter the value of your portfolio:")

position_size = float(portfolio_size) / len(final_dataframe.index)
for i in range(0, len(final_dataframe['Ticker'])-1):
    final_dataframe.loc[i, 'Number Of Shares to Buy'] = math.floor(position_size / final_dataframe['Price'][i])

# 6 Formatting Our Excel Output

writer = pd.ExcelWriter('recommended_trades.xlsx', engine='xlsxwriter')
final_dataframe.to_excel(writer, sheet_name='Recommended Trades', index = False)

# 7 Creating the Formats We'll Need For Our `.xlsx` File

"""

Formats include colors, fonts, and also symbols like `%` and `$`. We'll need four main formats for our Excel document:
* String format for tickers
* \\$XX.XX format for stock prices
* \\$XX,XXX format for market capitalization
* Integer format for the number of shares to purchase

"""
background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format(
        {
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

dollar_format = writer.book.add_format(
        {
            'num_format':'$0.00',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

integer_format = writer.book.add_format(
        {
            'num_format':'0',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

# 8 Applying the Formats to the Columns of Our `.xlsx` File

column_formats = { 
                    'A': ['Ticker', string_format],
                    'B': ['Price', dollar_format],
                    'C': ['Market Capitalization', dollar_format],
                    'D': ['Number of Shares to Buy', integer_format]
                    }

for column in column_formats.keys():
    writer.sheets['Recommended Trades'].set_column(f'{column}:{column}', 20, column_formats[column][1])
    writer.sheets['Recommended Trades'].write(f'{column}1', column_formats[column][0], string_format)

# 9 Save Excel Output

writer.save()