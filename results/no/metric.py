#!/usr/bin/env python3
"""
ChampSim Results Parser
Extracts metrics from ChampSim output and saves to CSV
Usage: python parse_champsim.py <input_file> <output_csv>
"""

import sys
import re
import csv

def parse_champsim_output(filename):
    """Parse ChampSim output file and extract metrics"""
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # Extract trace name
    trace_match = re.search(r'CPU 0 runs \.\./(traces/)?(.+?\.champsimtrace\.xz)', content)
    trace_name = trace_match.group(2) if trace_match else "Unknown"
    
    # Extract IPC
    ipc_match = re.search(r'CPU 0 cumulative IPC:\s+(\d+\.\d+)', content)
    ipc = float(ipc_match.group(1)) if ipc_match else 0.0
    
    # Extract L1D MPKI (LOAD MPKI)
    l1d_mpki_match = re.search(r'L1D LOAD.*?MPKI:\s+(\d+\.?\d*)', content)
    l1d_mpki = float(l1d_mpki_match.group(1)) if l1d_mpki_match else 0.0
    
    # Extract L2C MPKI (TOTAL)
    l2_mpki_match = re.search(r'L2C TOTAL.*?MPKI:\s+(\d+\.?\d*)', content)
    l2_mpki = float(l2_mpki_match.group(1)) if l2_mpki_match else 0.0
    
    # Extract LLC MPKI (TOTAL)
    llc_mpki_match = re.search(r'LLC TOTAL.*?MPKI:\s+(\d+\.?\d*)', content)
    llc_mpki = float(llc_mpki_match.group(1)) if llc_mpki_match else 0.0
    
    # Extract simulation time
    time_match = re.search(r'Simulation time:\s+(\d+)\s+hr\s+(\d+)\s+min\s+(\d+)\s+sec', content)
    if time_match:
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        seconds = int(time_match.group(3))
        sim_time = hours * 3600 + minutes * 60 + seconds
    else:
        sim_time = 0
    
    # Extract prefetch statistics (optional - for evaluating prefetcher)
    l2_prefetch_requested = 0
    l2_prefetch_useful = 0
    l2_prefetch_accuracy = 0.0
    
    prefetch_req_match = re.search(r'L2C PREFETCH\s+REQUESTED:\s+(\d+)', content)
    if prefetch_req_match:
        l2_prefetch_requested = int(prefetch_req_match.group(1))
    
    prefetch_useful_match = re.search(r'L2C USEFUL LOAD PREFETCHES:\s+(\d+)', content)
    if prefetch_useful_match:
        l2_prefetch_useful = int(prefetch_useful_match.group(1))
    
    prefetch_acc_match = re.search(r'L2C.*?ACCURACY:\s+(\d+\.?\d*)', content)
    if prefetch_acc_match:
        l2_prefetch_accuracy = float(prefetch_acc_match.group(1))
    
    return {
        'Trace': trace_name,
        'IPC': ipc,
        'L1D_MPKI': l1d_mpki,
        'L2_MPKI': l2_mpki,
        'LLC_MPKI': llc_mpki,
        'Simulation_Time(s)': sim_time,
        'L2_Prefetch_Requested': l2_prefetch_requested,
        'L2_Prefetch_Useful': l2_prefetch_useful,
        'L2_Prefetch_Accuracy': l2_prefetch_accuracy
    }

def main():
    if len(sys.argv) != 3:
        print("Usage: python parse_champsim.py <input_file> <output_csv>")
        print("Example: python parse_champsim.py results.txt metrics.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_csv = sys.argv[2]
    
    try:
        # Parse the results
        metrics = parse_champsim_output(input_file)
        
        # Write to CSV
        with open(output_csv, 'w', newline='') as csvfile:
            fieldnames = ['Trace', 'IPC', 'L1D_MPKI', 'L2_MPKI', 'LLC_MPKI', 
                         'Simulation_Time(s)', 'L2_Prefetch_Requested', 
                         'L2_Prefetch_Useful', 'L2_Prefetch_Accuracy']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerow(metrics)
        
        print(f"✓ Successfully parsed results")
        print(f"✓ Metrics saved to: {output_csv}")
        print(f"\nExtracted Metrics:")
        print(f"  Trace: {metrics['Trace']}")
        print(f"  IPC: {metrics['IPC']}")
        print(f"  L1D_MPKI: {metrics['L1D_MPKI']}")
        print(f"  L2_MPKI: {metrics['L2_MPKI']}")
        print(f"  LLC_MPKI: {metrics['LLC_MPKI']}")
        print(f"  Simulation Time: {metrics['Simulation_Time(s)']}s")
        if metrics['L2_Prefetch_Requested'] > 0:
            print(f"  L2 Prefetches: {metrics['L2_Prefetch_Requested']} "
                  f"(Useful: {metrics['L2_Prefetch_Useful']}, "
                  f"Accuracy: {metrics['L2_Prefetch_Accuracy']:.2f}%)")
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()