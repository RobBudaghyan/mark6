### backtester.py

import os
import pandas as pd
import numpy as np
from config import RESULTS_DIR

# Init backtest log folder
BACKTEST_LOGS_DIR = RESULTS_DIR + 'backtest_logs/'
os.makedirs(BACKTEST_LOGS_DIR, exist_ok=True)

def backtest_pair(pair_csv_file, start_date, end_date, Z_ENTRY=2.0, Z_EXIT=0.0):

    df = pd.read_csv(pair_csv_file, index_col=0, parse_dates=True)
    df.index.name = 'time'

    # Cut to selected window
    df = df.loc[start_date:end_date]

    # Handle empty case
    if df.empty:
        pair_name = os.path.basename(pair_csv_file).replace('_spread_z.csv', '')
        print(f"Skipping pair {pair_name} → no data in selected window")
        return {
            'pair': pair_name,
            'total_pnl': np.nan,
            'sharpe': np.nan,
            'max_dd': np.nan,
            'num_trades': 0,
            'win_rate': np.nan,
            'avg_duration_h': np.nan
        }

    # Prepare variables
    position = 0  # 0 = no position, 1 = long spread, -1 = short spread
    entry_price = None
    trades = []
    equity = [0]  # start at 0 PnL
    cum_pnl = 0

    for i in range(len(df)):

        z = df['zscore'].iloc[i]
        spread = df['spread'].iloc[i]
        time = df.index[i]

        # Entry logic
        if position == 0:
            if z > Z_ENTRY:
                position = -1  # short spread
                entry_price = spread
                entry_time = time
            elif z < -Z_ENTRY:
                position = 1   # long spread
                entry_price = spread
                entry_time = time

        # Exit logic
        elif position != 0:
            if (position == -1 and z <= Z_EXIT) or (position == 1 and z >= Z_EXIT):
                # Close position
                pnl = (entry_price - spread) if position == -1 else (spread - entry_price)
                trade_duration = (time - entry_time).total_seconds() / 3600  # in hours

                trades.append({
                    'entry_time': entry_time,
                    'exit_time': time,
                    'position': position,
                    'entry_z': df.loc[entry_time]['zscore'],
                    'exit_z': z,
                    'pnl': pnl,
                    'duration_h': trade_duration
                })

                cum_pnl += pnl
                equity.append(cum_pnl)

                position = 0
                entry_price = None

    # If still in position → close at last point
    if position != 0:
        final_spread = df['spread'].iloc[-1]
        pnl = (entry_price - final_spread) if position == -1 else (final_spread - entry_price)
        trade_duration = (df.index[-1] - entry_time).total_seconds() / 3600

        trades.append({
            'entry_time': entry_time,
            'exit_time': df.index[-1],
            'position': position,
            'entry_z': df.loc[entry_time]['zscore'],
            'exit_z': df['zscore'].iloc[-1],
            'pnl': pnl,
            'duration_h': trade_duration
        })

        cum_pnl += pnl
        equity.append(cum_pnl)

    # Save trade log
    pair_name = os.path.basename(pair_csv_file).replace('_spread_z.csv', '')
    trades_df = pd.DataFrame(trades)
    trades_df.to_csv(f'{BACKTEST_LOGS_DIR}{pair_name}_backtest_log.csv', index=False)

    # Save equity curve
    equity_df = pd.DataFrame({'equity': equity})
    equity_df['time'] = list(df.index[:len(equity_df)])
    equity_df.set_index('time', inplace=True)
    equity_df.to_csv(f'{BACKTEST_LOGS_DIR}{pair_name}_equity_curve.csv')

    # Compute summary stats
    total_pnl = equity[-1]
    returns = pd.Series(equity).diff().dropna()
    sharpe = returns.mean() / returns.std() * np.sqrt(252*24) if len(returns) > 1 else 0
    max_dd = (equity_df['equity'].cummax() - equity_df['equity']).max()

    num_trades = len(trades_df)
    win_rate = len(trades_df[trades_df['pnl'] > 0]) / num_trades if num_trades > 0 else 0
    avg_duration = trades_df['duration_h'].mean() if num_trades > 0 else 0

    summary = {
        'pair': pair_name,
        'total_pnl': total_pnl,
        'sharpe': sharpe,
        'max_dd': max_dd,
        'num_trades': num_trades,
        'win_rate': win_rate,
        'avg_duration_h': avg_duration
    }

    return summary

def backtest_top_pairs(top_pairs_file, start_date, end_date, Z_ENTRY=2.0, Z_EXIT=0.0):

    top_pairs_df = pd.read_csv(top_pairs_file)
    all_summaries = []

    for i, row in top_pairs_df.iterrows():
        pair_name = row['pair']
        pair_csv_file = f'{RESULTS_DIR}spreads/{pair_name.replace("-", "_")}_spread_z.csv'

        print(f"\nBacktesting pair: {pair_name}")
        summary = backtest_pair(pair_csv_file, start_date, end_date, Z_ENTRY, Z_EXIT)

        print(f"Summary: PnL={summary['total_pnl']:.2f} | Sharpe={summary['sharpe']:.2f} | MaxDD={summary['max_dd']:.2f} | "
              f"Trades={summary['num_trades']} | WinRate={summary['win_rate']:.2%} | AvgDur={summary['avg_duration_h']:.1f}h")

        all_summaries.append(summary)

    # Save all summaries to CSV
    summaries_df = pd.DataFrame(all_summaries)
    summaries_df.to_csv(f'{BACKTEST_LOGS_DIR}all_pairs_backtest_summary.csv', index=False)

    print("\nBacktest completed. Summary saved to all_pairs_backtest_summary.csv")
