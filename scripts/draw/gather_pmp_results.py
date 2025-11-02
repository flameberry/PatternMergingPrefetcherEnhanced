import pandas as pd
import sys

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
        get_singecore_coverage_accuracy, # Still need this for the logic
    )
    from workloads import workloads_all
except ImportError:
    print("Error: Could not find get_results.py or workloads.py.")
    print("Please make sure this script is in the same directory as get_results.py and workloads.py.")
    sys.exit(1)
except ImportError as e:
    print(f"Error importing from get_results: {e}")
    print("Please ensure get_raw_results and eliminate_invalid_values are defined in get_results.py")
    sys.exit(1)


# --- Configuration ---
# You can add more prefetchers here to compare them
prefetchers_to_run = ['no', 'pmp']
prefixes_to_use = {
    'no': 'aditya',
    'pmp': 'aditya'
    # 'prefetcher2': 'prefix_for_it',
}
# --- End Configuration ---


# --- 1. Get All Raw Data (Primary Change) ---
print("--- 1. Fetching All Raw Simulation Data ---")
try:
    (ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless,
     l2_pf_useful, l2_pf_useless, workloads_simplified) = get_raw_results(
        1, prefetchers_to_run, prefixes_to_use, workloads_all
    )
except Exception as e:
    print(f"Error during get_raw_results: {e}")
    print("This may be due to missing files or errors in get_results.py")
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
    print("Please check your file paths and if `get_raw_results` ran correctly.")
    sys.exit(1)

for workload in workloads_simplified:
    # Clean workload name
    # We find the prefix for 'pmp' and remove it.
    pmp_prefix = prefixes_to_use.get('pmp', 'aditya') # Default to 'aditya'
    clean_name = workload
    if workload.startswith(f"{pmp_prefix}-"):
        clean_name = workload[len(pmp_prefix)+1:]
    
    try:
        # --- Speedup ---
        cycles_no = cycles['no'][workload][0]
        cycles_pmp = cycles['pmp'][workload][0]
        
        speedup = 1.0 # Default to neutral
        if cycles_no > 0 and cycles_pmp > 0:
            speedup = cycles_no / cycles_pmp
        
        # --- Accuracy ---
        l2_useful = l2_pf_useful['pmp'][workload][0]
        l2_useless = l2_pf_useless['pmp'][workload][0]
        l1_useful = l1_pf_useful['pmp'][workload][0]
        l1_useless = l1_pf_useless['pmp'][workload][0]
        
        total_useful = l2_useful + l1_useful
        total_prefetches = total_useful + l2_useless + l1_useless
        
        accuracy = 0.0
        if total_prefetches > 0:
            accuracy = total_useful / total_prefetches
            
        # --- LLC Coverage ---
        baseline_misses = llc_load_miss['no'][workload][0]
        prefetcher_misses = llc_load_miss['pmp'][workload][0]
        
        coverage = 0.0
        if baseline_misses > 0:
            coverage_val = 1 - (prefetcher_misses / baseline_misses)
            coverage = max(0.0, coverage_val) # Don't let coverage be negative
        elif baseline_misses == 0:
            coverage = 1.0 if prefetcher_misses == 0 else 0.0
        
        per_workload_data.append({
            'workload': clean_name,
            'pmp_Speedup': speedup,
            'pmp_Accuracy': accuracy,
            'pmp_LLC_Coverage': coverage
        })
    
    except KeyError as e:
        print(f"KeyError processing workload '{workload}': {e}. This might mean 'no' or 'pmp' data is missing for this trace.")
    except Exception as e:
        print(f"Unexpected error processing workload '{workload}': {e}")

# Save detailed CSV
df_detail = pd.DataFrame(per_workload_data)
output_csv_detail = 'pmp_per_workload_metrics.csv'
df_detail.to_csv(output_csv_detail, index=False, float_format='%.4f')
print(f"Detailed per-workload metrics saved to {output_csv_detail}")

# --- 4. Calculate Overall Summary Metrics ---
print("\n--- 4. Calculating Overall Summary Metrics ---")

# GMean Speedup
valid_speedups = df_detail[df_detail['pmp_Speedup'].notna() & (df_detail['pmp_Speedup'] > 0)]['pmp_Speedup']
gmean_speedup = 1.0
if not valid_speedups.empty:
    gmean_speedup = gmean(valid_speedups)

# Mean Accuracy, Coverage
mean_accuracy = df_detail['pmp_Accuracy'].mean()
mean_coverage = df_detail['pmp_LLC_Coverage'].mean()

# Late Ratio (Needs raw data)
late_tmp = []
for workload in workloads_simplified:
    try:
        late_val = 0
        useful = l1_pf_useful['pmp'][workload][0]
        late = l1_pf_late['pmp'][workload][0]
        if useful > 0:
            late_val = late / useful
        late_tmp.append(late_val)
    except KeyError:
        # This workload was skipped earlier, skip it here too
        pass
mean_late_ratio = np.mean(late_tmp) if late_tmp else 0.0

summary_data = {
    'pmp_GMean_Speedup': gmean_speedup,
    'pmp_Mean_Accuracy': mean_accuracy,
    'pmp_Mean_LLC_Coverage': mean_coverage,
    'pmp_Mean_Late_Ratio': mean_late_ratio
}

df_summary = pd.DataFrame([summary_data])
output_csv_summary = 'pmp_overall_summary.csv'
df_summary.to_csv(output_csv_summary, index=False, float_format='%.4f')
print(f"Overall summary metrics saved to {output_csv_summary}")

print("\nData gathering complete.")

