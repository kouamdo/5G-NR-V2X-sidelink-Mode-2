import numpy as np
import pandas as pd
import argparse

def simulate_link(sinr_series_db, mcs=14, seed=42):
    
    np.random.seed(seed)
    
    sinr = np.array(sinr_series_db)
    sinr_clipped = np.clip(sinr, -5, 30)
    
    # Courbe BLER empirique FINALE : ajustée pour PDR simulé ≈ 58–59 %
    bler = np.zeros_like(sinr_clipped, dtype=float)
    
    bler[sinr_clipped < 0]   = 0.90   # très mauvais
    bler[(sinr_clipped >= 0) & (sinr_clipped < 5)]   = 0.25  # bas : 45 % perte
    bler[(sinr_clipped >= 5) & (sinr_clipped < 9)]   = 0.15   # zone inférieure : 35 % perte
    bler[(sinr_clipped >= 9) & (sinr_clipped < 12)]  = 0.10   # zone moyen : seulement 20 % perte
    bler[(sinr_clipped >= 12) & (sinr_clipped < 15)] = 0.03   # bon : 3 % perte
    bler[sinr_clipped >= 15] = 0.01   # très bon : 1 % perte
    
    # Petit bruit pour variabilité (réduit à 0.015 pour plus de stabilité)
    bler += np.random.normal(0, 0.015, len(bler))
    bler = np.clip(bler, 0, 1)
    
    successes = (np.random.rand(len(bler)) > bler).astype(int)
    return successes

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--csv', required=True)
    p.add_argument('--out', default='losses.csv')
    p.add_argument('--mcs', type=int, default=14)
    args = p.parse_args()

    df = pd.read_csv(args.csv)
    
    successes = simulate_link(df['sinr_db'].values, args.mcs)
    
    df['success'] = successes
    
    simulated_pdr = df['success'].mean()
    
    print(f"Simulation avec courbe empirique BLER (calibrée pour PDR réel ~58.83 %)")
    print(f"Generated success/loss sequence")
    print(f"Simulated PDR moyen : {simulated_pdr:.4f} ({simulated_pdr*100:.2f} %)")
    
    df.to_csv(args.out, index=False)
