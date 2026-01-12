import pandas as pd
import numpy as np
import argparse
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pkt_csv', default='pktTxRx.csv')
    parser.add_argument('--sinr_csv', default='pscchRxUePhy_full.csv')
    parser.add_argument('--output', default='traces/v2x_pdr_traces_fixed.csv')
    args = parser.parse_args()

    # Créer dossier si besoin
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Load pktTxRx
    pkt = pd.read_csv(args.pkt_csv, sep='|', header=None)
    pkt.columns = [
        'timeSec', 'txRx', 'nodeId', 'imsi', 'pktSizeBytes',
        'srcIp', 'srcPort', 'dstIp', 'dstPort', 'pktSeqNum',
        'SEED', 'RUN'
    ]
    print(f"Loaded pktTxRx: {pkt.shape[0]} rows")
    print(pkt.head(5))

    # Load pscchRxUePhy full
    sinr = pd.read_csv(args.sinr_csv, sep='|', header=None)
    sinr.columns = [
        'timeMs', 'cellId', 'rnti', 'bwpId', 'frame', 'subFrame', 'slot',
        'txRnti', 'dstL2Id', 'pscchRbStart', 'pscchRbLen', 'pscchMcs',
        'avrgSinr', 'minSinr', 'tbler', 'corrupt', 'psschStartSbCh',
        'psschLenSbCh', 'maxNumPerReserve', 'rsvpMs', 'SEED', 'RUN'
    ]
    sinr['timeSec'] = sinr['timeMs'] / 1000.0
    print(f"Loaded pscchRxUePhy: {sinr.shape[0]} rows")
    print(sinr[['timeSec', 'avrgSinr', 'minSinr', 'corrupt', 'tbler']].head(5))

    # PDR proxy from PHY Rx
    sinr['success'] = ((sinr['corrupt'] == 0) & (sinr['tbler'] == 0)).astype(int)
    total_rx_attempts = len(sinr)
    successful_rx = sinr['success'].sum()
    pdr_proxy_global = successful_rx / total_rx_attempts if total_rx_attempts > 0 else 0
    print(f"PSCCH Rx attempts: {total_rx_attempts}")
    print(f"Successful decodes: {successful_rx}")
    print(f"Global PDR proxy: {pdr_proxy_global:.4f}")

    # Index Datetime pour resample
    sinr['datetime'] = pd.to_datetime(sinr['timeSec'], unit='s')
    sinr.set_index('datetime', inplace=True)

    # PDR window (resample par 1s)
    window_pdr = sinr['success'].resample('1s').mean().reset_index().rename(columns={'success': 'window_pdr'})
    window_pdr['window_pdr'] = window_pdr['window_pdr'].rolling(window=10, min_periods=1).mean()
    window_pdr['timeSec'] = (window_pdr['datetime'] - pd.Timestamp('1970-01-01')).dt.total_seconds()

    # SINR approx dB avec clip
    sinr['sinr_db_approx'] = 10 * np.log10(sinr['avrgSinr'].clip(lower=1e-6, upper=1e6))
    mean_sinr_db = sinr['sinr_db_approx'].mean()

    # Base sur Tx
    tx_df = pkt[pkt['txRx'] == 'tx'].copy()
    tx_df['packet_sent'] = 1
    tx_df['packet_received'] = pdr_proxy_global  # proxy global

    # Nearest SINR per tx time (corrigé : diff en secondes)
    def get_nearest_sinr(tx_time):
        # Calcul de la différence en secondes (Timedelta → total_seconds)
        time_diff = (sinr.index - pd.to_datetime(tx_time, unit='s')).total_seconds()
        closest_idx = np.abs(time_diff).argmin()
        return sinr.iloc[closest_idx]['sinr_db_approx']

    tx_df['sinr_db'] = tx_df['timeSec'].apply(get_nearest_sinr)
    tx_df['mcs'] = 14

    # Merge window PDR (nearest)
    tx_df['datetime'] = pd.to_datetime(tx_df['timeSec'], unit='s')
    tx_df = pd.merge_asof(tx_df.sort_values('datetime'), window_pdr[['datetime', 'window_pdr']], on='datetime', direction='nearest').fillna(0)

    # Final columns
    final_df = tx_df[['timeSec', 'pktSeqNum', 'sinr_db', 'mcs', 'packet_sent', 'packet_received', 'window_pdr']].rename(columns={'pktSeqNum': 'seq_id'})

    final_df.to_csv(args.output, index=False)
    print(f"Exported {args.output} with {len(final_df)} rows (PDR proxy from PHY Rx)")
    print(f"Mean approx SINR (dB): {mean_sinr_db:.2f}")

if __name__ == '__main__':
    main()
