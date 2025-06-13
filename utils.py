### utils.py

import pandas as pd
import os
from config import DATA_DIR, RESAMPLE_TIMEFRAME

def load_ticker_csv(ticker_name):
    filepath = os.path.join(DATA_DIR, f'{ticker_name}.csv')
    df = pd.read_csv(
        filepath,
        usecols=[0, 1],
        names=['open_time', 'close'],
        skiprows=1,
        encoding='utf-8-sig',
        parse_dates=['open_time']
    )
    df.set_index('open_time', inplace=True)
    df = df.resample(RESAMPLE_TIMEFRAME).ffill().dropna()
    return df
