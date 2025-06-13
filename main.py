from backtester import backtest_top_pairs

if __name__ == "__main__":
    start_date = '2024-01-01'
    end_date = '2024-06-01'
    Z_ENTRY = 2.0
    Z_EXIT = 0.0

    backtest_top_pairs('results/top_pairs.csv', start_date, end_date, Z_ENTRY, Z_EXIT)
