### pair_selector.py

import os
import itertools
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from config import *
from utils import load_ticker_csv
import logging
from tqdm import tqdm

# Init folders
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(SPREADS_DIR, exist_ok=True)

# Init logging
logging.basicConfig(
    filename=f'{RESULTS_DIR}pair_selector.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def compute_zscore(spread, window):
    mean = spread.rolling(window).mean()
    std = spread.rolling(window).std()
    zscore = (spread - mean) / std
    return zscore

def filter_tickers():
    tickers = [f.replace('.csv', '') for f in os.listdir(DATA_DIR) if f.endswith('.csv')]

    good_tickers = []
    volatility_info = {}

    for ticker in tqdm(tickers, desc="Filtering tickers"):
        try:
            df = load_ticker_csv(ticker)

            history_days = (df.index[-1] - df.index[0]).days
            if history_days < MIN_HISTORY_DAYS:
                continue

            recent_df = df[-24*60:]

            volatility_pct = 100 * recent_df['close'].std() / recent_df['close'].mean()
            avg_price = recent_df['close'].mean()

            if volatility_pct < MIN_VOLATILITY_PCT:
                continue

            if avg_price < MIN_AVG_PRICE:
                continue

            good_tickers.append(ticker)

            # Save volatility info for filter
            lookback_window = VOLATILITY_LOOKBACK_DAYS * 24
            volatility_recent = df['close'].iloc[-lookback_window:].std()
            volatility_info[ticker] = volatility_recent

        except Exception as e:
            msg = f"Error processing ticker {ticker}: {e}"
            print(msg)
            logging.error(msg)

    msg = f"Selected {len(good_tickers)} good tickers out of {len(tickers)}"
    logging.info(msg)
    print(msg)

    # Apply volatility filter if enabled
    if USE_VOLATILITY_FILTER:
        sorted_tickers = sorted(volatility_info.items(), key=lambda x: x[1], reverse=True)
        top_tickers = [t[0] for t in sorted_tickers[:VOLATILITY_TOP_N]]

        msg = f"Using volatility filter → keeping top {VOLATILITY_TOP_N} tickers"
        logging.info(msg)
        print(msg)

        return top_tickers
    else:
        return good_tickers

def run_cointegration(good_tickers):
    pairs_results = []

    # Compute correlation matrix first
    price_data = {}

    print("Loading price data for correlation matrix...")
    for ticker in tqdm(good_tickers, desc="Loading prices"):
        try:
            df = load_ticker_csv(ticker)
            price_data[ticker] = df['close']
        except Exception as e:
            msg = f"Error loading ticker {ticker} for correlation: {e}"
            print(msg)
            logging.error(msg)

    price_df = pd.DataFrame(price_data).dropna()

    print("Computing correlation matrix...")
    corr_matrix = price_df.corr().abs()

    # Select pairs with corr > CORR_THRESHOLD
    pairs_to_test = []
    for ticker_a, ticker_b in itertools.combinations(good_tickers, 2):
        corr = corr_matrix.loc[ticker_a, ticker_b]
        if corr >= CORR_THRESHOLD:
            pairs_to_test.append((ticker_a, ticker_b))

    msg = f"[correlation filter] {len(pairs_to_test)} pairs passed correlation threshold ({CORR_THRESHOLD})"
    logging.info(msg)
    print(msg)

    # Run cointegration only on selected pairs
    for ticker_a, ticker_b in tqdm(pairs_to_test, desc="Running cointegration"):
        try:
            df_a = load_ticker_csv(ticker_a)
            df_b = load_ticker_csv(ticker_b)

            df = pd.merge(df_a, df_b, left_index=True, right_index=True, how='inner', suffixes=('_a', '_b'))

            if len(df) < MIN_HISTORY_DAYS * 24:
                continue

            x = df['close_a']
            y = df['close_b']

            beta = np.polyfit(x, y, 1)[0]
            spread = y - beta * x

            adf_pvalue = adfuller(spread.dropna())[1]

            if adf_pvalue < ADF_PVALUE_THRESHOLD:
                zscore = compute_zscore(spread, ZSCORE_LOOKBACK)

                out_df = pd.DataFrame({
                    'spread': spread,
                    'zscore': zscore
                })

                out_df.to_csv(f'{SPREADS_DIR}{ticker_a}_{ticker_b}_spread_z.csv')

                pairs_results.append({
                    'pair': f'{ticker_a}-{ticker_b}',
                    'adf_pvalue': adf_pvalue
                })

                msg = f"Found cointegrated pair: {ticker_a}-{ticker_b}, p-value={adf_pvalue:.4f}"
                print(msg)
                logging.info(msg)

        except Exception as e:
            msg = f"Error processing pair {ticker_a}-{ticker_b}: {e}"
            print(msg)
            logging.error(msg)

    pairs_df = pd.DataFrame(pairs_results).sort_values('adf_pvalue').head(TOP_N_PAIRS)
    pairs_df.to_csv(f'{RESULTS_DIR}top_pairs.csv', index=False)

    logging.info("Saved top pairs to results/top_pairs.csv")
    print("Saved top pairs to results/top_pairs.csv")
