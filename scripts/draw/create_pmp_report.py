# This script is a unified pipeline for PMP prefetcher evaluation.
# It merges the functionality of generate_pmp_reports.py and generate_pmp_graphs.py.
#
# 1. It fetches and processes raw simulation data.
# 2. It calculates per-workload and summary metrics.
# 3. It saves these metrics to CSV files.
# 4. It generates a comprehensive set of plots from the metrics.
# 5. All outputs (.csv, .png) are saved into a unique, timestamped
#    directory in the 'results/' folder at the project root to prevent overwrites.

import os
import sys
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from scipy.stats import gmean

# --- Important Dependencies ---
# This script assumes you have a get_results.py file in the same directory
# or in your Python path, and that it contains all the functions we are
# importing. It also assumes your workloads.py is available.
try:
    from get_results import (
        get_raw_results,
        eliminate_invalid_values,
    )
    from workloads import workloads_all
except ImportError:
    print("Error: Could not find get_results.py or workloads.py.", file=sys.stderr)
    print("Please make sure this script is in the same directory as get_results.py and workloads.py.", file=sys.stderr)
    sys.exit(1)

# --- Configuration ---
PREFIX = "aditya_20M_w5M"
PREFETCHERS_TO_RUN = ["no", "pmp"]
# --- End Configuration ---

def generate_reports(output_dir):
    """
    Fetches raw data, calculates metrics, saves them to CSV files,
    and returns the resulting dataframes.
    """
    print("--- 1. Fetching and Processing Simulation Data ---")
    
    prefixes_to_use = {p: PREFIX for p in PREFETCHERS_TO_RUN}

    try:
        (ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless, workloads_simplified) = get_raw_results(
            1, PREFETCHERS_TO_RUN, prefixes_to_use, workloads_all
        )
    except Exception as e:
        print(f"Error during get_raw_results: {e}", file=sys.stderr)
        return None, None

    print("--- 2. Cleaning and Processing Data ---")
    for d in [ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless]:
        eliminate_invalid_values(d, PREFETCHERS_TO_RUN, workloads_simplified)

    print("--- 3. Calculating Per-Workload Metrics ---")
    per_workload_data = []
    if not workloads_simplified:
        print("Error: 'workloads_simplified' is empty. No data to process.", file=sys.stderr)
        return None, None

    for workload in workloads_simplified:
        pmp_prefix = prefixes_to_use.get("pmp", PREFIX)
        clean_name = workload[len(pmp_prefix) + 1 :] if workload.startswith(f"{pmp_prefix}-") else workload

        try:
            cycles_no = cycles["no"][workload][0]
            cycles_pmp = cycles["pmp"][workload][0]
            speedup = cycles_no / cycles_pmp if cycles_no > 0 and cycles_pmp > 0 else 1.0

            l2_useful = l2_pf_useful["pmp"][workload][0]
            l2_useless = l2_pf_useless["pmp"][workload][0]
            l1_useful = l1_pf_useful["pmp"][workload][0]
            l1_useless = l1_pf_useless["pmp"][workload][0]

            total_useful = l2_useful + l1_useful
            total_prefetches = total_useful + l2_useless + l1_useless
            overall_accuracy = total_useful / total_prefetches if total_prefetches > 0 else 0.0

            l1_total = l1_useful + l1_useless
            l1_accuracy = l1_useful / l1_total if l1_total > 0 else 0.0
            l2_total = l2_useful + l2_useless
            l2_accuracy = l2_useful / l2_total if l2_total > 0 else 0.0

            baseline_misses = llc_load_miss["no"][workload][0]
            prefetcher_misses = llc_load_miss["pmp"][workload][0]
            coverage = 1 - (prefetcher_misses / baseline_misses) if baseline_misses > 0 else (1.0 if prefetcher_misses == 0 else 0.0)
            coverage = max(0.0, coverage)

            per_workload_data.append({
                "workload": clean_name, "pmp_Speedup": speedup, "pmp_Overall_Accuracy": overall_accuracy,
                "pmp_LLC_Coverage": coverage, "pmp_L1D_Accuracy": l1_accuracy, "pmp_L2C_Accuracy": l2_accuracy,
                "pmp_L1D_Useful": l1_useful, "pmp_L1D_Useless": l1_useless, "pmp_L2C_Useful": l2_useful,
                "pmp_L2C_Useless": l2_useless,
            })
        except KeyError as e:
            print(f"KeyError processing workload '{workload}': {e}. Skipping.", file=sys.stderr)

    df_detail = pd.DataFrame(per_workload_data)
    output_csv_detail = os.path.join(output_dir, "pmp_per_workload_metrics.csv")
    df_detail.to_csv(output_csv_detail, index=False, float_format="%.4f")
    print(f"Detailed metrics saved to {output_csv_detail}")

    print("--- 4. Calculating Overall Summary Metrics ---")
    valid_speedups = df_detail[df_detail["pmp_Speedup"].notna() & (df_detail["pmp_Speedup"] > 0)]["pmp_Speedup"]
    gmean_speedup = gmean(valid_speedups) if not valid_speedups.empty else 1.0

    late_tmp = []
    for workload in workloads_simplified:
        try:
            useful = l1_pf_useful["pmp"][workload][0]
            late = l1_pf_late["pmp"][workload][0]
            late_tmp.append(late / useful if useful > 0 else 0)
        except KeyError: pass
    mean_late_ratio = np.mean(late_tmp) if late_tmp else 0.0

    summary_data = {
        "pmp_GMean_Speedup": gmean_speedup,
        "pmp_Mean_Overall_Accuracy": df_detail["pmp_Overall_Accuracy"].mean(),
        "pmp_Mean_LLC_Coverage": df_detail["pmp_LLC_Coverage"].mean(),
        "pmp_Mean_Late_Ratio": mean_late_ratio,
        "pmp_Mean_L1D_Accuracy": df_detail["pmp_L1D_Accuracy"].mean(),
        "pmp_Mean_L2C_Accuracy": df_detail["pmp_L2C_Accuracy"].mean(),
        "pmp_Mean_L1D_Useful": df_detail["pmp_L1D_Useful"].mean(),
        "pmp_Mean_L1D_Useless": df_detail["pmp_L1D_Useless"].mean(),
        "pmp_Mean_L2C_Useful": df_detail["pmp_L2C_Useful"].mean(),
        "pmp_Mean_L2C_Useless": df_detail["pmp_L2C_Useless"].mean(),
    }
    df_summary = pd.DataFrame([summary_data])
    output_csv_summary = os.path.join(output_dir, "pmp_overall_summary.csv")
    df_summary.to_csv(output_csv_summary, index=False, float_format="%.4f")
    print(f"Overall summary saved to {output_csv_summary}")
    
    return df_detail, df_summary

def plot_speedup_bar(df, output_image):
    if df.empty or not all(c in df.columns for c in ['workload', 'pmp_Speedup']):
        print("Warning: Speedup data missing. Skipping speedup bar chart.", file=sys.stderr)
        return
    df = df.sort_values(by='pmp_Speedup', ascending=False)
    plt.figure(figsize=(max(12, len(df) * 0.4), 8))
    colors = ['#007acc' if x > 1.0 else '#cc3300' for x in df['pmp_Speedup']]
    plt.bar(df['workload'], df['pmp_Speedup'], color=colors, align='center')
    plt.axhline(y=1.0, color='grey', linestyle='--', linewidth=1)
    plt.title('PMP Prefetcher Speedup per Workload', fontsize=16, fontweight='bold')
    plt.ylabel('Speedup (Higher is Better)', fontsize=12)
    plt.xlabel('Workload', fontsize=12)
    plt.xticks(rotation=90, fontsize=8)
    plt.grid(axis='y', linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")

def plot_speedup_distribution(df, output_image):
    if 'pmp_Speedup' not in df or df['pmp_Speedup'].isnull().all():
        print("Warning: No valid speedup data. Skipping distribution plot.", file=sys.stderr)
        return
    plt.figure(figsize=(8, 6))
    plt.boxplot(df['pmp_Speedup'].dropna(), vert=False, patch_artist=True,
                boxprops=dict(facecolor='#007acc', alpha=0.7),
                medianprops=dict(color='yellow', linewidth=2))
    plt.axvline(x=1.0, color='red', linestyle='--', linewidth=1)
    plt.title('Distribution of PMP Speedups', fontsize=16, fontweight='bold')
    plt.xlabel('Speedup', fontsize=12)
    plt.yticks([])
    plt.grid(axis='x', linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")

def plot_accuracy_vs_speedup(df, output_image):
    if not all(c in df for c in ['pmp_Overall_Accuracy', 'pmp_Speedup']):
        print("Warning: Accuracy/Speedup data missing. Skipping scatter plot.", file=sys.stderr)
        return
    plt.figure(figsize=(10, 8))
    plt.scatter(df['pmp_Overall_Accuracy'], df['pmp_Speedup'], alpha=0.7, edgecolors='w')
    plt.axhline(y=1.0, color='grey', linestyle='--', linewidth=1)
    plt.title('Prefetcher Accuracy vs. Workload Speedup', fontsize=16, fontweight='bold')
    plt.xlabel('Per-Workload Accuracy', fontsize=12)
    plt.ylabel('Per-Workload Speedup', fontsize=12)
    plt.gca().xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")

def plot_radar_chart(df, output_image):
    try:
        speedup = df['pmp_GMean_Speedup'].iloc[0] - 1.0
        late_ratio = 1.0 - df['pmp_Mean_Late_Ratio'].iloc[0]
        metrics = {
            'Speedup': speedup, 'LLC Coverage': df['pmp_Mean_LLC_Coverage'].iloc[0],
            'Accuracy': df['pmp_Mean_Overall_Accuracy'].iloc[0], 'Timeliness': late_ratio
        }
    except (KeyError, IndexError) as e:
        print(f"Warning: Missing data for radar chart: {e}. Skipping.", file=sys.stderr)
        return
    labels = list(metrics.keys())
    values = [v if pd.notna(v) else 0 for v in metrics.values()]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist() + [0]
    values += values[:1]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='#007acc', alpha=0.25)
    ax.plot(angles, values, color='#007acc', linewidth=2)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    max_val = max(values) if values else 0
    ax.set_ylim(0, max(max_val * 1.2, 0.1))
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=12)
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.text(angle, value + (max_val * 0.05), f"{value:.1%}", ha='center', size=12, fontweight='bold')
    plt.title('Overall PMP Prefetcher Profile', fontsize=16, fontweight='bold', y=1.1)
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")

def plot_accuracy_coverage_summary(df, output_image):
    try:
        metrics = {
            'LLC Coverage': df['pmp_Mean_LLC_Coverage'].iloc[0],
            'L1D Accuracy': df['pmp_Mean_L1D_Accuracy'].iloc[0],
            'L2C Accuracy': df['pmp_Mean_L2C_Accuracy'].iloc[0]
        }
    except (KeyError, IndexError) as e:
        print(f"Warning: Missing data for accuracy/coverage plot: {e}. Skipping.", file=sys.stderr)
        return
    labels, values = list(metrics.keys()), list(metrics.values())
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, values, color=['#007acc', '#cc3300', '#009966'])
    plt.title('Overall Coverage and Accuracy', fontsize=16, fontweight='bold')
    plt.ylabel('Rate', fontsize=12)
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.ylim(0, 1.0)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, f'{yval:.1%}', ha='center', va='bottom', fontweight='bold')
    plt.grid(axis='y', linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")

def plot_useful_useless_summary(df, output_image):
    try:
        metrics = {
            'L1D Useful': df['pmp_Mean_L1D_Useful'].iloc[0], 'L1D Useless': df['pmp_Mean_L1D_Useless'].iloc[0],
            'L2C Useful': df['pmp_Mean_L2C_Useful'].iloc[0], 'L2C Useless': df['pmp_Mean_L2C_Useless'].iloc[0]
        }
    except (KeyError, IndexError) as e:
        print(f"Warning: Missing data for useful/useless plot: {e}. Skipping.", file=sys.stderr)
        return
    labels, values = list(metrics.keys()), list(metrics.values())
    plt.figure(figsize=(12, 7))
    plt.bar(labels, values, color=['#007acc', '#cc3300', '#009966', '#ff9900'])
    plt.yscale('log')
    plt.title('Average Useful and Useless Prefetches', fontsize=16, fontweight='bold')
    plt.ylabel('Number (Log Scale)', fontsize=12)
    for bar in plt.gca().patches:
        yval = bar.get_height()
        if yval > 0:
            plt.text(bar.get_x() + bar.get_width()/2.0, yval * 1.1, f'{yval:,.0f}', ha='center', va='bottom')
    plt.grid(axis='y', linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")

def plot_l1_l2_accuracy_bar(df, output_image):
    if df.empty or not all(c in df.columns for c in ['workload', 'pmp_L1D_Accuracy', 'pmp_L2C_Accuracy']):
        print("Warning: L1/L2 Accuracy data missing. Skipping chart.", file=sys.stderr)
        return
    df = df.sort_values(by='pmp_Overall_Accuracy', ascending=False)
    n_workloads = len(df['workload'])
    index = np.arange(n_workloads)
    bar_width = 0.35
    fig, ax = plt.subplots(figsize=(max(12, n_workloads * 0.6), 8))
    ax.bar(index - bar_width/2, df['pmp_L1D_Accuracy'], bar_width, label='L1D Accuracy', color='#007acc')
    ax.bar(index + bar_width/2, df['pmp_L2C_Accuracy'], bar_width, label='L2C Accuracy', color='#009966')
    ax.set_xlabel('Workload', fontsize=12)
    ax.set_ylabel('Accuracy', fontsize=12)
    ax.set_title('PMP L1D vs L2C Prefetch Accuracy', fontsize=16, fontweight='bold')
    ax.set_xticks(index)
    ax.set_xticklabels(df['workload'], rotation=90, fontsize=8)
    ax.legend()
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(axis='y', linestyle=':', alpha=0.7)
    fig.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")

def generate_graphs(df_detail, df_summary, output_dir):
    """Generates and saves all plots."""
    print("\n--- 5. Generating All PMP Graphs ---")
    
    plot_functions = {
        'pmp_speedup_per_workload.png': (plot_speedup_bar, df_detail),
        'pmp_speedup_distribution.png': (plot_speedup_distribution, df_detail),
        'pmp_accuracy_vs_speedup.png': (plot_accuracy_vs_speedup, df_detail),
        'pmp_l1_l2_accuracy.png': (plot_l1_l2_accuracy_bar, df_detail),
        'pmp_overall_metrics_radar.png': (plot_radar_chart, df_summary),
        'pmp_accuracy_coverage_summary.png': (plot_accuracy_coverage_summary, df_summary),
        'pmp_useful_useless_summary.png': (plot_useful_useless_summary, df_summary),
    }
    
    for filename, (plot_func, df) in plot_functions.items():
        if df is not None and not df.empty:
            plot_func(df, os.path.join(output_dir, filename))
        else:
            print(f"Warning: Dataframe for {filename} is empty. Skipping plot.", file=sys.stderr)
            
    print("\nGraph generation complete.")

def create_output_directory():
    """Creates a timestamped directory for the results at the project root."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dir_name = f"pmp_results_{timestamp}"
    try:
        # Assumes this script is in scripts/draw, so ../../ is the project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        output_dir = os.path.join(project_root, 'results', dir_name)
        os.makedirs(output_dir, exist_ok=True)
        print(f"Results will be saved in: {output_dir}")
        return output_dir
    except Exception as e:
        print(f"Error creating output directory: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    output_directory = create_output_directory()
    if not output_directory:
        sys.exit(1)
        
    df_detail, df_summary = generate_reports(output_directory)
    
    if df_detail is not None and df_summary is not None:
        generate_graphs(df_detail, df_summary, output_directory)
    else:
        print("Could not generate graphs because data generation failed.", file=sys.stderr)

    print("\n--- PMP Report Generation Complete ---")
