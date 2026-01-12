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
    print(sinr[['timeSec', 'avrgSinr', 'minSinr', 'corrupt', 'tbler']].head
