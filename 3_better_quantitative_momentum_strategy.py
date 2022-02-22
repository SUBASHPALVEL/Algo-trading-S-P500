"""

author SubashPalvel 

* High-quality momentum stocks show "slow and steady" outperformance over long periods of time.

* Low-quality momentum stocks might not show any momentum for a long time, and then surge upwards.

The reason why high-quality momentum stocks are preferred is because low-quality momentum can often be cause by short-term news that is unlikely to be repeated in the future.

To identify high-quality momentum, we're going to build a strategy that selects stocks from the highest percentiles of: 

* 1-month price returns
* 3-month price returns
* 6-month price returns
* 1-year price returns


"""

# 1 import statements

import numpy as np 
import pandas as pd 
import requests 
import xlsxwriter 
import math 
from scipy import stats

# 2 import S&P_500 file

stocks = pd.read_csv('S&P_500.csv')

# 3 Acquiring an API Token

IEX_CLOUD_API_TOKEN = 'Tpk_059b97af715d417d9f49f50b51b1c448' 

# 4 Adding Our Stocks Data to a Pandas DataFrame using Batch API Call

def chunks(lst, n):
    #Yield successive n-sized chunks from lst
    for i in range(0, len(lst), n):
        yield lst[i:i + n]   
        
symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))

hqm_columns = [
    'Ticker',
    'Price',
    'One-Year Price Return',
    'One-Year Return Percentile',
    'Six-Month Price Return',
    'Six-Month Return Percentile',
    'Three-Month Price Return',
    'Three-Month Return Percentile',
    'One-Month Price Return',
    'One-Month Return Percentile'
]

hqm_dataframe = pd.DataFrame(columns=hqm_columns)
convert_none = lambda x : 0 if x is None else x

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=price,stats&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    
    for symbol in symbol_string.split(','):
        hqm_dataframe = hqm_dataframe.append(
            pd.Series(
                [
                    symbol,
                    data[symbol]['price'],
                    convert_none(data[symbol]['stats']['year1ChangePercent']),
                    'N/A',
                    convert_none(data[symbol]['stats']['month6ChangePercent']),
                    'N/A',
                    convert_none(data[symbol]['stats']['month3ChangePercent']),
                    'N/A',
                    convert_none(data[symbol]['stats']['month1ChangePercent']),
                    'N/A'
                ],
                index = hqm_columns
            ),
            ignore_index=True
        )
        
# 5 Calculating Momentum Percentiles

time_periods = [
                'One-Year',
                'Six-Month',
                'Three-Month',
                'One-Month'
                ]

for row in hqm_dataframe.index:
    for time_period in time_periods:
        hqm_dataframe.loc[row, f'{time_period} Return Percentile'] = stats.percentileofscore(hqm_dataframe[f'{time_period} Price Return'], hqm_dataframe.loc[row, f'{time_period} Price Return'])/100

# 6 Calculating the HQM Score

             #The `HQM Score` will be the arithmetic mean of the 4 momentum percentile scores 

from statistics import mean

for row in hqm_dataframe.index:
    momentum_percentiles = []
    for time_period in time_periods:
        momentum_percentiles.append(hqm_dataframe.loc[row, f'{time_period} Return Percentile'])
    hqm_dataframe.loc[row, 'HQM Score'] = mean(momentum_percentiles)

# 7 Selecting the 50 Best Momentum Stocks

hqm_dataframe.sort_values('HQM Score', ascending = False, inplace=True)
hqm_dataframe = hqm_dataframe[:51]

# 8 Formatting Our Excel Output

writer = pd.ExcelWriter('momentum_strategy.xlsx', engine='xlsxwriter')
hqm_dataframe.to_excel(writer, sheet_name='Momentum Strategy', index = False)

# 9 Creating the Formats 

background_color = '#0a0a23'
font_color = '#ffffff'

string_template = writer.book.add_format(
        {
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

dollar_template = writer.book.add_format(
        {
            'num_format':'$0.00',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

integer_template = writer.book.add_format(
        {
            'num_format':'0',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

percent_template = writer.book.add_format(
        {
            'num_format':'0.0%',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

# 10 Applying the templates

column_formats = { 
                    'A': ['Ticker', string_template],
                    'B': ['Price', dollar_template],
                    'C': ['One-Year Price Return', percent_template],
                    'D': ['One-Year Return Percentile', percent_template],
                    'E': ['Six-Month Price Return', percent_template],
                    'F': ['Six-Month Return Percentile', percent_template],
                    'G': ['Three-Month Price Return', percent_template],
                    'H': ['Three-Month Return Percentile', percent_template],
                    'I': ['One-Month Price Return', percent_template],
                    'J': ['One-Month Return Percentile', percent_template],
                    'K': ['HQM Score', integer_template]
                    }

for column in column_formats.keys():
    writer.sheets['Momentum Strategy'].set_column(f'{column}:{column}', 20, column_formats[column][1])
    writer.sheets['Momentum Strategy'].write(f'{column}1', column_formats[column][0], string_template)

# 11 Save Excel Output

writer.save()







