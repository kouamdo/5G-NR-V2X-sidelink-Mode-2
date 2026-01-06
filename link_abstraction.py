import numpy as np
import pandas as pd
import argparse

def simulate_link(sinr_series_db, mcs=14, seed=42):
    np.random.seed(seed)
    # Sigmoid BLER approx (tune threshold based on MCS; ~8-12 dB for 50% BLER at MCS14)
    threshold = 10.0 if mcs == 14 else 8.0
    slope = 1.0
    bler = 1 / (1 + np.exp(slope * (np.array(sinr_series_db) - threshold)))
    return (np.random.rand(len(bler)) > bler).astype(int)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--csv', required=True, help='Exported CSV with sinr_db')
    p.add_argument('--out', default='success_losses.csv')
    p.add_argument('--mcs', type=int, default=14)
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    successes = simulate_link(df['sinr_db'].values, args.mcs)
    df['success'] = successes
    df.to_csv(args.out, index=False)
    print("Generated success/loss sequence")
