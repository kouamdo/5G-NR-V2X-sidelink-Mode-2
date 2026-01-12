import numpy as np
import pandas as pd
import argparse

def simulate_link(sinr_series_db, mcs=14, seed=42):
    np.random.seed(seed)
    
    # VALEURS CALIBRÉES pour PDR simulé ≈ 58.83 %
    threshold = 13.0      # seuil haut pour que SINR moyen 9 dB donne ~59 % succès
    slope = 0.08          # pente très douce pour étaler les pertes
    
    sinr_clipped = np.clip(np.array(sinr_series_db), -10, 30)
    bler = 1 / (1 + np.exp(slope * (sinr_clipped - threshold)))
    successes = (np.random.rand(len(bler)) > bler).astype(int)
    
    return successes, threshold, slope

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--csv', required=True)
    p.add_argument('--out', default='losses.csv')
    p.add_argument('--mcs', type=int, default=14)
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    
    successes, threshold, slope = simulate_link(df['sinr_db'].values, args.mcs)
    
    df['success'] = successes
    
    simulated_pdr = df['success'].mean()
    print(f"Simulation avec threshold={threshold} dB, slope={slope}, seed=42")
    print(f"Generated success/loss sequence")
    print(f"Simulated PDR moyen : {simulated_pdr:.4f} ({simulated_pdr*100:.2f} %)")
    
    df.to_csv(args.out, index=False)
