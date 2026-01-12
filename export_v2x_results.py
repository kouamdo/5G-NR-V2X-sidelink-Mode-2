import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='default-nr-v2x-west-to-east-highway.db')
    parser.add_argument('--output', default='v2x_basic_pdr.csv')
    args = parser.parse_args()

    # Connect to DB
    conn = pd.read_sql("SELECT * FROM pktTxRx", f"sqlite:///{args.db}")

    # Rename/organize columns (adjust based on your actual headers; from sample: time,type,tx_id?,rx_id?,size,src_ip,src_port,dst_ip,dst_port,seq,sent,received)
    # Assume columns are unnamed or indexed; pd.read_sql names them 0,1,2,...
    conn.columns = ['time', 'type', 'tx_id', 'rx_id', 'size', 'src_ip', 'src_port', 'dst_ip', 'dst_port', 'seq', 'packet_sent', 'packet_received']

    # Filter only relevant (tx and rx rows if separate, but here tx rows include received flag)
    df = conn[conn['type'] == 'tx'].copy()
    df['mcs'] = 14  # fixed from Tx MAC logs; can join with pscchTxUeMac if needed
    df['sinr_db'] = 15.0  # placeholder (no direct SINR; next step add approximation or parse PHY tables)
    df['window_pdr'] = df.groupby('rx_id')['packet_received'].rolling(window=10, min_periods=1).mean().reset_index(0, drop=True)

    df.to_csv(args.output, index=False)
    print(f"Exported to {args.output} with {len(df)} rows")

if __name__ == '__main__':
    main()
