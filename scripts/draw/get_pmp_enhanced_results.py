import pandas as pd
import sys
import numpy as np
from scipy.stats import gmean

# --- Important ---
# This script assumes you have a get_results.py file in the same directory
# or in your Python path, and that it contains all the functions we are
# importing. It also assumes your workloads.py is available.

try:
    from get_results import (
        get_raw_results,
        eliminate_invalid_values,
    )
    from workloads import workloads_all
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please make sure get_results.py and workloads.py exist and are correct.")
    sys.exit(1)


# --- Configuration ---
prefetchers_to_run = ['no', 'pmp', 'pmp_enhanced']
prefixes_to_use = {
    'no': 'manish',
    'pmp': 'manish',
    'pmp_enhanced': 'manish'
}
# --- End Configuration ---


# --- 1. Get All Raw Data ---
print("--- 1. Fetching All Raw Simulation Data ---")
try:
    (ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless,
     l2_pf_useful, l2_pf_useless, workloads_simplified) = get_raw_results(
        1, prefetchers_to_run, prefixes_to_use, workloads_all
    )
except Exception as e:
    print(f"Error during get_raw_results: {e}")
    sys.exit(1)

# --- 2. Clean and Process Data ---
print("--- 2. Cleaning and Processing Data ---")
for d in [ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless]:
    eliminate_invalid_values(d, prefetchers_to_run, workloads_simplified)

# --- 3. Calculate Per-Workload Metrics ---
print("--- 3. Calculating Per-Workload Metrics ---")
per_workload_data = []

if not workloads_simplified:
    print("Error: 'workloads_simplified' is empty. No data to process.")
    sys.exit(1)

for workload in workloads_simplified:
    clean_name = workload
    # Remove any prefix for naming clarity
    for pf in prefetchers_to_run:
        prefix = prefixes_to_use.get(pf, 'manish')
        if workload.startswith(f"{prefix}-"):
            clean_name = workload[len(prefix)+1:]
    
    metrics_for_workload = {'workload': clean_name}

    for pf in prefetchers_to_run:
        if pf == 'no':
            continue  # Skip baseline for metrics
        
        try:
            # --- Speedup ---
            cycles_baseline = cycles['no'][workload][0]
            cycles_pf = cycles[pf][workload][0]
            speedup = 1.0
            if cycles_baseline > 0 and cycles_pf > 0:
                speedup = cycles_baseline / cycles_pf
            
            # --- Prefetcher Accuracy ---
            l1_useful_val = l1_pf_useful[pf][workload][0]
            l1_useless_val = l1_pf_useless[pf][workload][0]
            l2_useful_val = l2_pf_useful[pf][workload][0]
            l2_useless_val = l2_pf_useless[pf][workload][0]
            
            total_useful = l1_useful_val + l2_useful_val
            total_prefetches = total_useful + l1_useless_val + l2_useless_val
            overall_accuracy = total_useful / total_prefetches if total_prefetches > 0 else 0.0
            
            l1_total = l1_useful_val + l1_useless_val
            l1_accuracy = l1_useful_val / l1_total if l1_total > 0 else 0.0
            
            l2_total = l2_useful_val + l2_useless_val
            l2_accuracy = l2_useful_val / l2_total if l2_total > 0 else 0.0
            
            # --- LLC Coverage ---
            baseline_misses = llc_load_miss['no'][workload][0]
            pf_misses = llc_load_miss[pf][workload][0]
            coverage = 0.0
            if baseline_misses > 0:
                coverage = max(0.0, 1 - (pf_misses / baseline_misses))
            elif baseline_misses == 0:
                coverage = 1.0 if pf_misses == 0 else 0.0
            
            # --- Save metrics ---
            metrics_for_workload.update({
                f'{pf}_Speedup': speedup,
                f'{pf}_Overall_Accuracy': overall_accuracy,
                f'{pf}_LLC_Coverage': coverage,
                f'{pf}_L1D_Accuracy': l1_accuracy,
                f'{pf}_L2C_Accuracy': l2_accuracy,
                f'{pf}_L1D_Useful': l1_useful_val,
                f'{pf}_L1D_Useless': l1_useless_val,
                f'{pf}_L2C_Useful': l2_useful_val,
                f'{pf}_L2C_Useless': l2_useless_val
            })
        
        except KeyError as e:
            print(f"KeyError for workload '{workload}' and prefetcher '{pf}': {e}")
        except Exception as e:
            print(f"Unexpected error for workload '{workload}' and prefetcher '{pf}': {e}")
    
    per_workload_data.append(metrics_for_workload)

# Save detailed CSV
df_detail = pd.DataFrame(per_workload_data)
output_csv_detail = 'per_workload_metrics.csv'
df_detail.to_csv(output_csv_detail, index=False, float_format='%.4f')
print(f"Detailed per-workload metrics saved to {output_csv_detail}")

# --- 4. Calculate Overall Summary Metrics ---
print("\n--- 4. Calculating Overall Summary Metrics ---")
summary_data = {}

for pf in prefetchers_to_run:
    if pf == 'no':
        continue
    
    valid_speedups = df_detail[df_detail[f'{pf}_Speedup'].notna() & (df_detail[f'{pf}_Speedup'] > 0)][f'{pf}_Speedup']
    gmean_speedup = gmean(valid_speedups) if not valid_speedups.empty else 1.0
    
    mean_overall_accuracy = df_detail[f'{pf}_Overall_Accuracy'].mean()
    mean_coverage = df_detail[f'{pf}_LLC_Coverage'].mean()
    mean_l1_accuracy = df_detail[f'{pf}_L1D_Accuracy'].mean()
    mean_l2_accuracy = df_detail[f'{pf}_L2C_Accuracy'].mean()
    mean_l1_useful = df_detail[f'{pf}_L1D_Useful'].mean()
    mean_l1_useless = df_detail[f'{pf}_L1D_Useless'].mean()
    mean_l2_useful = df_detail[f'{pf}_L2C_Useful'].mean()
    mean_l2_useless = df_detail[f'{pf}_L2C_Useless'].mean()
    
    # --- Late ratio ---
    late_tmp = []
    for workload in workloads_simplified:
        try:
            useful = l1_pf_useful[pf][workload][0]
            late = l1_pf_late[pf][workload][0]
            late_val = late / useful if useful > 0 else 0.0
            late_tmp.append(late_val)
        except KeyError:
            continue
    mean_late_ratio = np.mean(late_tmp) if late_tmp else 0.0
    
    summary_data.update({
        f'{pf}_GMean_Speedup': gmean_speedup,
        f'{pf}_Mean_Overall_Accuracy': mean_overall_accuracy,
        f'{pf}_Mean_LLC_Coverage': mean_coverage,
        f'{pf}_Mean_Late_Ratio': mean_late_ratio,
        f'{pf}_Mean_L1D_Accuracy': mean_l1_accuracy,
        f'{pf}_Mean_L2C_Accuracy': mean_l2_accuracy,
        f'{pf}_Mean_L1D_Useful': mean_l1_useful,
        f'{pf}_Mean_L1D_Useless': mean_l1_useless,
        f'{pf}_Mean_L2C_Useful': mean_l2_useful,
        f'{pf}_Mean_L2C_Useless': mean_l2_useless
    })

    df_summary = pd.DataFrame([summary_data])
    # output_csv_summary = 'overall_summary.csv'
    df_summary.to_csv(f'{pf}_overall_summary.csv', index=False, float_format='%.4f')
    print(f"Overall summary metrics saved to {pf}_overall_summary.csv")

print("\nData gathering complete.")
