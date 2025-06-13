### config.py

# Parameters for filtering and cointegration testing

# Filtering thresholds
MIN_HISTORY_DAYS = 30  # You wanted to test fast inefficiencies → reduced from 180
MIN_VOLATILITY_PCT = 1.0  # std dev % over recent window
MIN_AVG_PRICE = 0.05      # discard "dead" tickers

# Correlation filter
CORR_THRESHOLD = 0.8  # only test pairs with |corr| > threshold

# Volatility filter
USE_VOLATILITY_FILTER = True
VOLATILITY_LOOKBACK_DAYS = 30  # lookback window in days
VOLATILITY_TOP_N = 50          # keep only top N volatile tickers

# Cointegration test
ADF_PVALUE_THRESHOLD = 0.05

# Max number of pairs to save (top N)
TOP_N_PAIRS = 50

# Data directory
DATA_DIR = 'data/'

# Results directory
RESULTS_DIR = 'results/'
SPREADS_DIR = RESULTS_DIR + 'spreads/'

# Sampling params
RESAMPLE_TIMEFRAME = '1h'  # fixed FutureWarning: use 'h'

# Z-score window
ZSCORE_LOOKBACK = 60
