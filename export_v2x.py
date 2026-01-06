import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pkt_csv', default='pktTxRx.csv')
    parser.add_argument('--sinr_csv', default='pscchRxUePhy.csv')
    parser.add_argument('--output', default='v2x_pdr_traces.csv')
    args = parser.parse_args()

    # Load pktTxRx - pipe-separated, no header
    pkt = pd.read_csv(args.pkt_csv, sep='|', header=None)
    # Assign column names from schema
    pkt.columns = [
        'timeSec', 'txRx', 'nodeId', 'imsi', 'pktSizeBytes',
        'srcIp', 'srcPort', 'dstIp', 'dstPort', 'pktSeqNum',
        'SEED', 'RUN'
    ]

    print(f"Loaded pktTxRx: {pkt.shape[0]} rows")
    print(pkt.head(5))  # debug

    # Load pscchRxUePhy - same, pipe-separated, no header
    sinr = pd.read_csv(args.sinr_csv, sep='|', header=None)
    sinr.columns = [
        'timeMs', 'cellId', 'rnti', 'bwpId', 'frame', 'subFrame', 'slot',
        'txRnti', 'dstL2Id', 'pscchRbStart', 'pscchRbLen', 'pscchMcs',
        'avrgSinr', 'minSinr', 'tbler', 'corrupt', 'psschStartSbCh',
        'psschLenSbCh', 'maxNumPerReserve', 'rsvpMs', 'SEED', 'RUN'
    ]
    # Convert timeMs to seconds for alignment
    sinr['timeSec'] = sinr['timeMs'] / 1000.0

    print(f"Loaded pscchRxUePhy: {sinr.shape[0]} rows")
    print(sinr[['timeSec', 'avrgSinr', 'minSinr', 'corrupt']].head(5))  # debug

    # Basic PDR computation from pktTxRx
    # Group by pktSeqNum to match sent vs received
    sent = pkt[pkt['txRx'] == 'tx'].groupby('pktSeqNum').size().reset_index(name='sent_count')
    received = pkt[pkt['txRx'] == 'rx'].groupby('pktSeqNum').size().reset_index(name='received_count')

    pdr_df = pd.merge(sent, received, on='pktSeqNum', how='left').fillna(0)
    pdr_df['pdr'] = pdr_df['received_count'] / pdr_df['sent_count']

    # Approximate time for each seq (use min time of tx for that seq)
    tx_times = pkt[pkt['txRx'] == 'tx'][['pktSeqNum', 'timeSec']].groupby('pktSeqNum')['timeSec'].min().reset_index()
    pdr_df = pd.merge(pdr_df, tx_times, on='pktSeqNum')

    # Add mean SINR (global for simplicity; can match by nearest time later)
    mean_sinr = sinr['avrgSinr'].mean()
    pdr_df['sinr_db'] = mean_sinr
    pdr_df['mcs'] = 14  # fixed default
    pdr_df['packet_sent'] = pdr_df['sent_count']
    pdr_df['packet_received'] = pdr_df['received_count']
    pdr_df['window_pdr'] = pdr_df['pdr'].rolling(window=10, min_periods=1).mean()

    # Select and rename to match test requirement
    final_df = pdr_df[['timeSec', 'pktSeqNum', 'sinr_db', 'mcs',
                       'packet_sent', 'packet_received', 'window_pdr']].rename(columns={'pktSeqNum': 'seq_id'})

    final_df.to_csv(args.output, index=False)
    print(f"Exported {args.output} with {len(final_df)} rows (PDR aggregated per packet sequence)")

if __name__ == '__main__':
    main()
