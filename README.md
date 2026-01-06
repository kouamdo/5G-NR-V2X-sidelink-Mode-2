# 5G NR Sidelink Mode 2 Link Abstraction Prototype

This is a minimal working prototype for **5G NR V2X sidelink Mode 2** link abstraction, as per the test assignment. It uses ns-3 + 5G-LENA (NR-V2X extension) to simulate a basic V2X scenario, exports packet delivery and SINR metrics, and applies a simple link abstraction model to simulate packet success/loss.

## Chosen Stack
- **Simulator**: ns-3 (branch `v2x-lte-dev`) + NR module (branch `nr-v2x-dev`)
- **Why**: Official CTTC NR-V2X implementation with direct support for sidelink Mode 2 (autonomous resource allocation, sensing-based), periodic broadcast traffic (CAM-like), and KPI output in SQLite.
- **Limitations**: 
  - SINR extracted from PSCCH Rx (control channel), not PSSCH/data (PSSCH Rx table empty in short runs).
  - Current sim shows ~100% PDR (good conditions); needs longer/more degraded runs for visible BLER.
  - Approximation only (no HARQ, no advanced fading, no Sionna integration yet).

## Prerequisites
- Ubuntu 22.04/24.04 VM
- ns-3 built with `./ns3 configure --enable-examples --enable-tests` and `./ns3 build`
- Python 3 + pandas + numpy (`pip install pandas numpy`)

## How to Run

### 1. Run the simulation (Mode 2 sidelink, highway scenario)
```bash
# Basic short run (2 UEs, good conditions)
./ns3 run "nr-v2x-west-to-east-highway --simTime=20 --numVehiclesPerLane=1 --numLanes=2 --interVehicleDist=30 --logging=true"

# Degraded run (more interesting losses)
./ns3 run "nr-v2x-west-to-east-highway --simTime=100 --numVehiclesPerLane=1 --numLanes=2 --interVehicleDist=120 --txPower=5 --logging=true"

```

### 2. Export traces to CSV

Export packet events (pktTxRx) and SINR proxy (pscchRxUePhy) + compute PDR/abstraction-ready format:
```bash
# Export raw tables
sqlite3 default-nr-v2x-west-to-east-highway.db \
  "SELECT * FROM pktTxRx ORDER BY timeSec;" > pktTxRx.csv

sqlite3 default-nr-v2x-west-to-east-highway.db \
  "SELECT timeMs/1000.0 AS timeSec, txRnti, rnti, avrgSinr, minSinr, corrupt, tbler FROM pscchRxUePhy ORDER BY timeMs;" > pscchRxUePhy.csv

# Process to final CSV (PDR, approx SINR dB, rolling window)
python3 export_v2x.py --pkt_csv=pktTxRx.csv --sinr_csv=pscchRxUePhy.csv --output traces/v2x_pdr_traces.csv

```

### 3. Link Abstraction

Input: CSV with sinr_db column
Output: same CSV + success column (1 = delivered, 0 = lost)
Uses reproducible random seed + clipping to avoid numerical issues.


```bash
python3 link_abstraction.py --csv traces/v2x_pdr_traces.csv --mcs 14 --out traces/losses.csv
