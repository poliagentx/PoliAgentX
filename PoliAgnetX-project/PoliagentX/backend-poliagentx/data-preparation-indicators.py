import pandas as pd
import numpy as np
import os

data = pd.read_csv('https://raw.githubusercontent.com/oguerrer/ppi/main/tutorials/raw_data/raw_indicators.csv')

normalised_series = []
years = [column_name for column_name in data.columns if str(column_name).isnumeric()]
for index, row in data.iterrows():
    time_series = row[years].values
    normalised_serie = (time_series - row.worstBound)/(row.bestBound - row.worstBound)
    if row.invert == 1:
        final_serie = 1 - normalised_serie
    else:
        final_serie = normalised_serie
    normalised_series.append( final_serie )
    
df = pd.DataFrame(normalised_series, columns=years)

df['seriesCode'] = data.seriesCode
df['sdg'] = data.sdg
df['minVals'] = np.zeros(len(data))
df['maxVals'] = np.ones(len(data))
df['instrumental'] = data.instrumental
df['seriesName'] = data.seriesName
df['color'] = data.color

# add new columns
df['I0'] = df[years[0]]
df['IF'] = df[years[-1]]
successRates = np.sum(df[years].values[:,1::] > df[years].values[:,0:-1], axis=1)/(len(years)-1)

# if a success rate is 0 or 1, it is recommended to replace them by a very low or high value as 
# zeros and ones are usually an artefact of lacking data on enough policy trials in the indicator
successRates[successRates==0] = .05
successRates[successRates==1] = .95
df['successRates'] = successRates

df.loc[df.I0==df.IF, 'IF'] = df.loc[df.I0==df.IF, 'IF']*1.05
df['qm'] = -0.33 # quality of monitoring
df['rl'] = -0.33 # quality of the rule of law

os.makedirs('clean_data', exist_ok=True)
df.to_csv('clean_data/data_indicators.csv', index=False)