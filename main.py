### main.py

from pair_selector import filter_tickers, run_cointegration

if __name__ == "__main__":
    good_tickers = filter_tickers()
    run_cointegration(good_tickers)