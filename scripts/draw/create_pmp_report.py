# (Aditya): This script is a unified pipeline for PMP prefetcher evaluation.
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
import argparse
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
    print(
        "Please make sure this script is in the same directory as get_results.py and workloads.py.",
        file=sys.stderr,
    )
    sys.exit(1)

# --- Configuration ---
PREFIX = "aditya_warmup5000000_sim200000000"
PREFETCHERS_TO_RUN = ["no", "pmp"]
# --- End Configuration ---


def generate_reports(output_dir, num_cores=1):
    """
    Fetches raw data, calculates metrics, saves them to CSV files,
    and returns the resulting dataframes.
    """
    print(f"1. Fetching and Processing Simulation Data (Cores: {num_cores})")

    prefixes_to_use = {p: PREFIX for p in PREFETCHERS_TO_RUN}

    try:
        (
            ipc,
            cycles,
            llc_load_miss,
            l1_pf_late,
            l1_pf_useful,
            l1_pf_useless,
            l2_pf_useful,
            l2_pf_useless,
            workloads_simplified,
            l1d_load_miss,
            l2c_load_miss,
        ) = get_raw_results(
            num_cores, PREFETCHERS_TO_RUN, prefixes_to_use, workloads_all
        )
    except Exception as e:
        print(f"Error during get_raw_results: {e}", file=sys.stderr)
        return None, None

    print("--- 2. Cleaning and Processing Data ---")
    for d in [
        ipc,
        cycles,
        llc_load_miss,
        l1_pf_late,
        l1_pf_useful,
        l1_pf_useless,
        l2_pf_useful,
        l2_pf_useless,
        l1d_load_miss,
        l2c_load_miss,
    ]:
        eliminate_invalid_values(d, PREFETCHERS_TO_RUN, workloads_simplified)

    print("--- 3. Calculating Per-Workload Metrics ---")
    per_workload_data = []
    if not workloads_simplified:
        print(
            "Error: 'workloads_simplified' is empty. No data to process.",
            file=sys.stderr,
        )
        return None, None

    for workload in workloads_simplified:
        pmp_prefix = prefixes_to_use.get("pmp", PREFIX)
        clean_name = (
            workload[len(pmp_prefix) + 1 :]
            if workload.startswith(f"{pmp_prefix}-")
            else workload
        )

        try:
            # Aggregate data across all cores for this workload
            # For cycles, taking the MAX cycles across cores determines the makespan of the workload mix
            cycles_no = max(cycles["no"][workload])
            cycles_pmp = max(cycles["pmp"][workload])

            # For IPC, we calculate System IPC: Sum(Instructions) / Max(Cycles)
            # Since get_raw_results returns pre-calculated IPC per core (instr/cycles),
            # we can't just sum them if cycles differ.
            # However, get_raw_results computes IPC = instr/cycles.
            # Let's approximate System IPC roughly as sum of individual IPCs for simplicity,
            # or better: verify if get_raw_results gives instructions.
            # It currently gives 'ipc' and 'cycles'. Instructions = ipc * cycles.

            instr_no = sum(
                [
                    ipc["no"][workload][i] * cycles["no"][workload][i]
                    for i in range(num_cores)
                ]
            )
            instr_pmp = sum(
                [
                    ipc["pmp"][workload][i] * cycles["pmp"][workload][i]
                    for i in range(num_cores)
                ]
            )

            system_ipc_no = instr_no / cycles_no if cycles_no > 0 else 0
            system_ipc_pmp = instr_pmp / cycles_pmp if cycles_pmp > 0 else 0

            speedup = system_ipc_pmp / system_ipc_no if system_ipc_no > 0 else 1.0

            # Sum counts across all cores
            l2_useful = sum(l2_pf_useful["pmp"][workload])
            l2_useless = sum(l2_pf_useless["pmp"][workload])
            l1_useful = sum(l1_pf_useful["pmp"][workload])
            l1_useless = sum(l1_pf_useless["pmp"][workload])

            total_useful = l2_useful + l1_useful
            total_prefetches = total_useful + l2_useless + l1_useless
            overall_accuracy = (
                total_useful / total_prefetches if total_prefetches > 0 else 0.0
            )

            l1_total = l1_useful + l1_useless
            l1_accuracy = l1_useful / l1_total if l1_total > 0 else 0.0
            l2_total = l2_useful + l2_useless
            l2_accuracy = l2_useful / l2_total if l2_total > 0 else 0.0

            # LLC Coverage (Sum misses across cores)
            baseline_misses_llc = sum(llc_load_miss["no"][workload])
            prefetcher_misses_llc = sum(llc_load_miss["pmp"][workload])
            coverage_llc = (
                1 - (prefetcher_misses_llc / baseline_misses_llc)
                if baseline_misses_llc > 0
                else (1.0 if prefetcher_misses_llc == 0 else 0.0)
            )
            coverage_llc = max(0.0, coverage_llc)

            # L1D Coverage
            baseline_misses_l1 = sum(l1d_load_miss["no"][workload])
            prefetcher_misses_l1 = sum(l1d_load_miss["pmp"][workload])
            coverage_l1 = (
                1 - (prefetcher_misses_l1 / baseline_misses_l1)
                if baseline_misses_l1 > 0
                else (1.0 if prefetcher_misses_l1 == 0 else 0.0)
            )
            coverage_l1 = max(0.0, coverage_l1)

            # L2C Coverage
            baseline_misses_l2 = sum(l2c_load_miss["no"][workload])
            prefetcher_misses_l2 = sum(l2c_load_miss["pmp"][workload])
            coverage_l2 = (
                1 - (prefetcher_misses_l2 / baseline_misses_l2)
                if baseline_misses_l2 > 0
                else (1.0 if prefetcher_misses_l2 == 0 else 0.0)
            )
            coverage_l2 = max(0.0, coverage_l2)

            per_workload_data.append(
                {
                    "workload": clean_name,
                    "ipc_no": system_ipc_no,
                    "ipc_pmp": system_ipc_pmp,
                    "pmp_Speedup": speedup,
                    "pmp_Overall_Accuracy": overall_accuracy,
                    "pmp_LLC_Coverage": coverage_llc,
                    "pmp_L1D_Coverage": coverage_l1,
                    "pmp_L2C_Coverage": coverage_l2,
                    "pmp_L1D_Accuracy": l1_accuracy,
                    "pmp_L2C_Accuracy": l2_accuracy,
                    "pmp_L1D_Useful": l1_useful,
                    "pmp_L1D_Useless": l1_useless,
                    "pmp_L2C_Useful": l2_useful,
                    "pmp_L2C_Useless": l2_useless,
                }
            )
        except KeyError as e:
            print(
                f"KeyError processing workload '{workload}': {e}. Skipping.",
                file=sys.stderr,
            )

    df_detail = pd.DataFrame(per_workload_data)
    output_csv_detail = os.path.join(output_dir, "pmp_per_workload_metrics.csv")
    df_detail.to_csv(output_csv_detail, index=False, float_format="%.4f")
    print(f"Detailed metrics saved to {output_csv_detail}")

    print("--- 4. Calculating Overall Summary Metrics ---")
    valid_speedups = df_detail[
        df_detail["pmp_Speedup"].notna() & (df_detail["pmp_Speedup"] > 0)
    ]["pmp_Speedup"]
    gmean_speedup = gmean(valid_speedups) if not valid_speedups.empty else 1.0

    late_tmp = []
    for workload in workloads_simplified:
        try:
            # Sum useful/late across cores for aggregation
            useful = sum(l1_pf_useful["pmp"][workload])
            late = sum(l1_pf_late["pmp"][workload])
            late_tmp.append(late / useful if useful > 0 else 0)
        except KeyError:
            pass
    mean_late_ratio = np.mean(late_tmp) if late_tmp else 0.0

    summary_data = {
        "pmp_GMean_Speedup": gmean_speedup,
        "pmp_Mean_Baseline_IPC": df_detail["ipc_no"].mean(),
        "pmp_Mean_PMP_IPC": df_detail["ipc_pmp"].mean(),
        "pmp_Mean_Overall_Accuracy": df_detail["pmp_Overall_Accuracy"].mean(),
        "pmp_Mean_LLC_Coverage": df_detail["pmp_LLC_Coverage"].mean(),
        "pmp_Mean_L1D_Coverage": df_detail["pmp_L1D_Coverage"].mean(),
        "pmp_Mean_L2C_Coverage": df_detail["pmp_L2C_Coverage"].mean(),
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
    if df.empty or not all(c in df.columns for c in ["workload", "pmp_Speedup"]):
        print(
            "Warning: Speedup data missing. Skipping speedup bar chart.",
            file=sys.stderr,
        )
        return

    df = df.sort_values(by="pmp_Speedup", ascending=False)
    plt.figure(figsize=(max(12, len(df) * 0.1), 4))
    colors = ["#007acc" if x > 1.0 else "#cc3300" for x in df["pmp_Speedup"]]
    plt.bar(df["workload"], df["pmp_Speedup"], color=colors, width=0.6)
    plt.axhline(y=1.0, color="grey", linestyle="--", linewidth=0.8)
    plt.title(
        "PMP Prefetcher Speedup per Workload", fontsize=12, fontweight="bold", pad=10
    )
    plt.ylabel("Speedup", fontsize=10)
    plt.xlabel("Workload", fontsize=10)
    plt.xticks(rotation=90, fontsize=4)
    plt.yticks(fontsize=8)
    plt.grid(axis="y", linestyle=":", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def plot_speedup_distribution(df, output_image):
    if "pmp_Speedup" not in df or df["pmp_Speedup"].isnull().all():
        print(
            "Warning: No valid speedup data. Skipping distribution plot.",
            file=sys.stderr,
        )
        return
    plt.figure(figsize=(8, 6))
    plt.boxplot(
        df["pmp_Speedup"].dropna(),
        vert=False,
        patch_artist=True,
        boxprops=dict(facecolor="#007acc", alpha=0.7),
        medianprops=dict(color="yellow", linewidth=2),
    )
    plt.axvline(x=1.0, color="red", linestyle="--", linewidth=1)
    plt.title("Distribution of PMP Speedups", fontsize=16, fontweight="bold")
    plt.xlabel("Speedup", fontsize=12)
    plt.yticks([])
    plt.grid(axis="x", linestyle=":", alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def plot_accuracy_vs_speedup(df, output_image):
    if not all(c in df for c in ["pmp_Overall_Accuracy", "pmp_Speedup"]):
        print(
            "Warning: Accuracy/Speedup data missing. Skipping scatter plot.",
            file=sys.stderr,
        )
        return
    plt.figure(figsize=(10, 8))
    plt.scatter(
        df["pmp_Overall_Accuracy"], df["pmp_Speedup"], alpha=0.7, edgecolors="w"
    )
    plt.axhline(y=1.0, color="grey", linestyle="--", linewidth=1)
    plt.title(
        "Prefetcher Accuracy vs. Workload Speedup", fontsize=16, fontweight="bold"
    )
    plt.xlabel("Per-Workload Accuracy", fontsize=12)
    plt.ylabel("Per-Workload Speedup", fontsize=12)
    plt.gca().xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.grid(True, linestyle=":", alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def plot_radar_chart(df, output_image):
    try:
        speedup = df["pmp_GMean_Speedup"].iloc[0] - 1.0
        late_ratio = 1.0 - df["pmp_Mean_Late_Ratio"].iloc[0]
        metrics = {
            "Speedup": speedup,
            "LLC Coverage": df["pmp_Mean_LLC_Coverage"].iloc[0],
            "Accuracy": df["pmp_Mean_Overall_Accuracy"].iloc[0],
            "Timeliness": late_ratio,
        }
    except (KeyError, IndexError) as e:
        print(f"Warning: Missing data for radar chart: {e}. Skipping.", file=sys.stderr)
        return
    labels = list(metrics.keys())
    values = [v if pd.notna(v) else 0 for v in metrics.values()]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist() + [0]
    values += values[:1]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color="#007acc", alpha=0.25)
    ax.plot(angles, values, color="#007acc", linewidth=2)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    max_val = max(values) if values else 0
    ax.set_ylim(0, max(max_val * 1.2, 0.1))
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=12)
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.text(
            angle,
            value + (max_val * 0.05),
            f"{value:.1%}",
            ha="center",
            size=12,
            fontweight="bold",
        )
    plt.title("Overall PMP Prefetcher Profile", fontsize=16, fontweight="bold", y=1.1)
    plt.savefig(output_image, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def plot_accuracy_coverage_summary(df, output_image):
    try:
        # Reconstruct metrics dictionary in the requested order:
        # L1D Acc, L1D Cov, L2C Acc, L2C Cov, LLC Cov
        metrics = {}
        
        metrics["L1D Accuracy"] = df["pmp_Mean_L1D_Accuracy"].iloc[0]
        
        if "pmp_Mean_L1D_Coverage" in df.columns:
            metrics["L1D Coverage"] = df["pmp_Mean_L1D_Coverage"].iloc[0]
            
        metrics["L2C Accuracy"] = df["pmp_Mean_L2C_Accuracy"].iloc[0]
        
        if "pmp_Mean_L2C_Coverage" in df.columns:
            metrics["L2C Coverage"] = df["pmp_Mean_L2C_Coverage"].iloc[0]
            
        metrics["LLC Coverage"] = df["pmp_Mean_LLC_Coverage"].iloc[0]

    except (KeyError, IndexError) as e:
        print(
            f"Warning: Missing data for accuracy/coverage plot: {e}. Skipping.",
            file=sys.stderr,
        )
        return

    labels, values = list(metrics.keys()), list(metrics.values())
    plt.figure(figsize=(max(10, len(labels) * 2), 6))

    # Extended color palette for up to 5 metrics
    # Blue, Red, Green, Purple, Orange
    colors = ["#007acc", "#cc3300", "#009966", "#9933cc", "#ff9900"]

    bars = plt.bar(labels, values, color=colors[: len(labels)])
    plt.title("Overall Coverage and Accuracy", fontsize=16, fontweight="bold")
    plt.ylabel("Rate", fontsize=12)
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.ylim(0, 1.0)
    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + 0.02,
            f"{yval:.1%}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )
    plt.grid(axis="y", linestyle=":", alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def plot_useful_useless_summary(df, output_image):
    try:
        metrics = {
            "L1D Useful": df["pmp_Mean_L1D_Useful"].iloc[0],
            "L1D Useless": df["pmp_Mean_L1D_Useless"].iloc[0],
            "L2C Useful": df["pmp_Mean_L2C_Useful"].iloc[0],
            "L2C Useless": df["pmp_Mean_L2C_Useless"].iloc[0],
        }
    except (KeyError, IndexError) as e:
        print(
            f"Warning: Missing data for useful/useless plot: {e}. Skipping.",
            file=sys.stderr,
        )
        return
    labels, values = list(metrics.keys()), list(metrics.values())
    plt.figure(figsize=(12, 7))
    plt.bar(labels, values, color=["#007acc", "#cc3300", "#009966", "#ff9900"])
    plt.yscale("log")
    plt.title("Average Useful and Useless Prefetches", fontsize=16, fontweight="bold")
    plt.ylabel("Number (Log Scale)", fontsize=12)
    for bar in plt.gca().patches:
        yval = bar.get_height()
        if yval > 0:
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                yval * 1.1,
                f"{yval:,.0f}",
                ha="center",
                va="bottom",
            )
    plt.grid(axis="y", linestyle=":", alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def plot_l1_l2_accuracy_bar(df, output_image):
    if df.empty or not all(
        c in df.columns for c in ["workload", "pmp_L1D_Accuracy", "pmp_L2C_Accuracy"]
    ):
        print("Warning: L1/L2 Accuracy data missing. Skipping chart.", file=sys.stderr)
        return
    df = df.sort_values(by="pmp_Overall_Accuracy", ascending=False)
    n_workloads = len(df["workload"])
    index = np.arange(n_workloads)
    bar_width = 0.35
    fig, ax = plt.subplots(figsize=(max(12, n_workloads * 0.6), 8))
    ax.bar(
        index - bar_width / 2,
        df["pmp_L1D_Accuracy"],
        bar_width,
        label="L1D Accuracy",
        color="#007acc",
    )
    ax.bar(
        index + bar_width / 2,
        df["pmp_L2C_Accuracy"],
        bar_width,
        label="L2C Accuracy",
        color="#009966",
    )
    ax.set_xlabel("Workload", fontsize=12)
    ax.set_ylabel("Accuracy", fontsize=12)
    ax.set_title("PMP L1D vs L2C Prefetch Accuracy", fontsize=16, fontweight="bold")
    ax.set_xticks(index)
    ax.set_xticklabels(df["workload"], rotation=90, fontsize=8)
    ax.legend()
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(axis="y", linestyle=":", alpha=0.7)
    fig.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def plot_ipc_comparison_bar(df, output_image):
    if df.empty or not all(c in df.columns for c in ["workload", "ipc_no", "ipc_pmp"]):
        print(
            "Warning: IPC data missing. Skipping IPC comparison bar chart.",
            file=sys.stderr,
        )
        return

    df = df.sort_values(by="pmp_Speedup", ascending=False)
    n_workloads = len(df["workload"])
    index = np.arange(n_workloads)
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(max(12, n_workloads * 0.6), 8))
    ax.bar(
        index - bar_width / 2,
        df["ipc_no"],
        bar_width,
        label="Baseline IPC (no prefetcher)",
        color="#cc3300",
    )
    ax.bar(
        index + bar_width / 2,
        df["ipc_pmp"],
        bar_width,
        label="PMP IPC",
        color="#007acc",
    )

    ax.set_xlabel("Workload", fontsize=12)
    ax.set_ylabel("Instructions Per Cycle (IPC)", fontsize=12)
    ax.set_title("Baseline IPC vs. PMP IPC", fontsize=16, fontweight="bold")
    ax.set_xticks(index)
    ax.set_xticklabels(df["workload"], rotation=90, fontsize=8)
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.7)

    fig.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def generate_graphs(df_detail, df_summary, output_dir):
    """Generates and saves all plots."""
    print("\n--- 5. Generating All PMP Graphs ---")

    plot_functions = {
        "pmp_ipc_comparison.png": (plot_ipc_comparison_bar, df_detail),
        "pmp_speedup_per_workload.png": (plot_speedup_bar, df_detail),
        "pmp_speedup_distribution.png": (plot_speedup_distribution, df_detail),
        "pmp_accuracy_vs_speedup.png": (plot_accuracy_vs_speedup, df_detail),
        "pmp_l1_l2_accuracy.png": (plot_l1_l2_accuracy_bar, df_detail),
        "pmp_overall_metrics_radar.png": (plot_radar_chart, df_summary),
        "pmp_accuracy_coverage_summary.png": (
            plot_accuracy_coverage_summary,
            df_summary,
        ),
        "pmp_useful_useless_summary.png": (plot_useful_useless_summary, df_summary),
    }

    for filename, (plot_func, df) in plot_functions.items():
        if df is not None and not df.empty:
            plot_func(df, os.path.join(output_dir, filename))
        else:
            print(
                f"Warning: Dataframe for {filename} is empty. Skipping plot.",
                file=sys.stderr,
            )

    print("\nGraph generation complete.")


def generate_comparison_graphs(merged_df, output_dir):
    """Generates all comparison plots."""
    print("--- 7. Generating Comparison Graphs ---")

    comparison_plots = {
        "comparison_ipc_3way.png": plot_ipc_comparison_3way,
        "comparison_speedup.png": plot_speedup_comparison,
        "comparison_accuracy.png": plot_accuracy_comparison,
        "comparison_coverage.png": plot_coverage_comparison,
        "comparison_summary.png": plot_summary_comparison,
    }

    for filename, plot_func in comparison_plots.items():
        if not merged_df.empty:
            plot_func(merged_df, os.path.join(output_dir, filename))
        else:
            print(
                f"Warning: Merged dataframe for {filename} is empty. Skipping comparison plot.",
                file=sys.stderr,
            )


def plot_summary_comparison(df, output_image):
    # Define the metrics and their order
    # Format: (Display Label, Column Base Name)
    desired_metrics = [
        ("L1D Accuracy", "accuracy_l1d"),
        ("L1D Coverage", "coverage_l1d"),
        ("L2C Accuracy", "accuracy_l2c"),
        ("L2C Coverage", "coverage_l2c"),
        ("LLC Coverage", "coverage_llc"),
    ]

    labels = []
    default_means = []
    adaptive_means = []

    # Calculate means for available columns
    for label, base in desired_metrics:
        col_def = f"{base}_default"
        col_adap = f"{base}_adaptive"
        
        if col_def in df.columns and col_adap in df.columns:
            labels.append(label)
            default_means.append(df[col_def].mean())
            adaptive_means.append(df[col_adap].mean())

    if not labels:
        print("Warning: No summary metrics found for comparison.", file=sys.stderr)
        return

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(max(10, len(labels) * 2), 6))
    
    rects1 = ax.bar(x - width/2, default_means, width, label='Default', color='#ffc107')
    rects2 = ax.bar(x + width/2, adaptive_means, width, label='Adaptive', color='#007acc')

    ax.set_ylabel('Rate')
    ax.set_title('Overall Performance Summary Comparison', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_ylim(0, 1.05)
    ax.grid(axis='y', linestyle=':', alpha=0.7)

    # Add value labels on top of bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1%}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def plot_ipc_comparison_3way(df, output_image):
    if not all(
        c in df.columns for c in ["workload", "ipc_no", "ipc_default", "ipc_adaptive"]
    ):
        print(
            "Warning: Missing data for 3-way IPC comparison. Skipping plot.",
            file=sys.stderr,
        )
        return

    df_sorted = df.sort_values(by="speedup_adaptive", ascending=False)
    n_workloads = len(df_sorted)
    index = np.arange(n_workloads)
    bar_width = 0.25

    fig, ax = plt.subplots(figsize=(max(12, n_workloads * 0.6), 7))
    ax.bar(
        index - bar_width,
        df_sorted["ipc_no"],
        bar_width,
        label="Baseline (no)",
        color="#6c757d",
    )
    ax.bar(
        index, df_sorted["ipc_default"], bar_width, label="Default PMP", color="#ffc107"
    )
    ax.bar(
        index + bar_width,
        df_sorted["ipc_adaptive"],
        bar_width,
        label="Adaptive PMP",
        color="#007acc",
    )

    ax.set_xlabel("Workload", fontsize=12)
    ax.set_ylabel("Instructions Per Cycle (IPC)", fontsize=12)
    ax.set_title(
        "IPC Comparison: Baseline vs. Default PMP vs. Adaptive PMP",
        fontsize=16,
        fontweight="bold",
    )
    ax.set_xticks(index)
    ax.set_xticklabels(df_sorted["workload"], rotation=90, fontsize=8)
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.7)
    fig.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def plot_speedup_comparison(df, output_image):
    if not all(
        c in df.columns for c in ["workload", "speedup_default", "speedup_adaptive"]
    ):
        print(
            "Warning: Missing data for speedup comparison. Skipping plot.",
            file=sys.stderr,
        )
        return

    df_sorted = df.sort_values(by="speedup_adaptive", ascending=False)
    n_workloads = len(df_sorted)
    index = np.arange(n_workloads)
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(max(12, n_workloads * 0.6), 7))
    ax.bar(
        index - bar_width / 2,
        df_sorted["speedup_default"],
        bar_width,
        label="Default PMP Speedup",
        color="#ffc107",
    )
    ax.bar(
        index + bar_width / 2,
        df_sorted["speedup_adaptive"],
        bar_width,
        label="Adaptive PMP Speedup",
        color="#007acc",
    )

    ax.axhline(y=1.0, color="grey", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Workload", fontsize=12)
    ax.set_ylabel("Speedup (over baseline)", fontsize=12)
    ax.set_title(
        "Speedup Comparison: Default PMP vs. Adaptive PMP",
        fontsize=16,
        fontweight="bold",
    )
    ax.set_xticks(index)
    ax.set_xticklabels(df_sorted["workload"], rotation=90, fontsize=8)
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.7)
    fig.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def plot_accuracy_comparison(df, output_image):
    # Define the desired order of metrics
    potential_metrics = [
        ("L1D Accuracy", "accuracy_l1d"),
        ("L1D Coverage", "coverage_l1d"),
        ("L2C Accuracy", "accuracy_l2c"),
        ("L2C Coverage", "coverage_l2c"),
    ]

    # Filter based on what is actually in the dataframe
    metrics = []
    for title, base in potential_metrics:
        if f"{base}_default" in df.columns and f"{base}_adaptive" in df.columns:
            metrics.append((title, base))

    if not metrics:
        print(
            "Warning: Missing data for accuracy/coverage comparison. Skipping plot.",
            file=sys.stderr,
        )
        return

    df_sorted = df.sort_values(by="speedup_adaptive", ascending=False)
    n_workloads = len(df_sorted)
    index = np.arange(n_workloads)
    bar_width = 0.35

    # Dynamically calculate height: 5 inches per subplot
    fig, axes = plt.subplots(
        len(metrics),
        1,
        figsize=(max(12, n_workloads * 0.4), 5 * len(metrics)),
        sharex=True,
    )

    # Handle single subplot case where axes is not a list
    if len(metrics) == 1:
        axes = [axes]

    for i, (title, metric_base) in enumerate(metrics):
        axes[i].bar(
            index - bar_width / 2,
            df_sorted[f"{metric_base}_default"],
            bar_width,
            label="Default",
            color="#ffc107",
        )
        axes[i].bar(
            index + bar_width / 2,
            df_sorted[f"{metric_base}_adaptive"],
            bar_width,
            label="Adaptive",
            color="#007acc",
        )

        # Determine Y-axis label based on metric type
        y_label = "Accuracy" if "Accuracy" in title else "Coverage"
        axes[i].set_ylabel(y_label)
        axes[i].set_title(title)
        axes[i].legend()
        axes[i].grid(axis="y", linestyle=":", alpha=0.7)
        axes[i].yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

        # Calculate max value for ylim, ensuring at least 1.0
        max_val = (
            df_sorted[[f"{metric_base}_default", f"{metric_base}_adaptive"]].max().max()
        )
        axes[i].set_ylim(0, max(1.0, max_val * 1.1))

    plt.xlabel("Workload")
    plt.xticks(index, df_sorted["workload"], rotation=90, fontsize=8)
    fig.suptitle(
        "PMP Accuracy & L1/L2 Coverage Comparison: Default vs. Adaptive",
        fontsize=16,
        fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def plot_coverage_comparison(df, output_image):
    # Determine which coverage metrics are available
    metrics = []
    # Reordered: L1D, L2C, LLC
    if "coverage_l1d_default" in df.columns and "coverage_l1d_adaptive" in df.columns:
        metrics.append(("L1D Coverage", "coverage_l1d"))
    if "coverage_l2c_default" in df.columns and "coverage_l2c_adaptive" in df.columns:
        metrics.append(("L2C Coverage", "coverage_l2c"))
    if "coverage_llc_default" in df.columns and "coverage_llc_adaptive" in df.columns:
        metrics.append(("LLC Coverage", "coverage_llc"))

    if not metrics:
        print(
            "Warning: No complete coverage pairs found for comparison. Skipping coverage plot.",
            file=sys.stderr,
        )
        return

    df_sorted = df.sort_values(by="speedup_adaptive", ascending=False)
    n_workloads = len(df_sorted)
    index = np.arange(n_workloads)
    bar_width = 0.35

    # Adjust figure size based on number of metrics
    fig, axes = plt.subplots(
        len(metrics),
        1,
        figsize=(max(12, n_workloads * 0.4), 6 * len(metrics)),
        sharex=True,
    )

    # If only one metric, axes is not a list, so wrap it
    if len(metrics) == 1:
        axes = [axes]

    for i, (title, metric_base) in enumerate(metrics):
        axes[i].bar(
            index - bar_width / 2,
            df_sorted[f"{metric_base}_default"],
            bar_width,
            label="Default",
            color="#ffc107",
        )
        axes[i].bar(
            index + bar_width / 2,
            df_sorted[f"{metric_base}_adaptive"],
            bar_width,
            label="Adaptive",
            color="#007acc",
        )
        axes[i].set_ylabel("Coverage")
        axes[i].set_title(title)
        axes[i].legend()
        axes[i].grid(axis="y", linestyle=":", alpha=0.7)
        axes[i].yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        axes[i].set_ylim(0, 1.05)

    plt.xlabel("Workload")
    plt.xticks(index, df_sorted["workload"], rotation=90, fontsize=8)
    fig.suptitle(
        "PMP Coverage Comparison: Default vs. Adaptive", fontsize=16, fontweight="bold"
    )
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved {os.path.basename(output_image)}")


def generate_comparison_report(current_df, compare_dir, output_dir):
    """Loads a previous report and generates comparison graphs."""
    print("\n--- 6. Generating Comparison Report ---")
    comparison_csv_path = os.path.join(compare_dir, "pmp_per_workload_metrics.csv")
    if not os.path.exists(comparison_csv_path):
        print(
            f"Error: Could not find 'pmp_per_workload_metrics.csv' in '{compare_dir}'",
            file=sys.stderr,
        )
        return

    # Load the comparison dataframe (default PMP)
    default_df = pd.read_csv(comparison_csv_path)

    # Define potential mappings
    potential_renames = {
        "ipc_pmp": "ipc_default",
        "pmp_Speedup": "speedup_default",
        "pmp_Overall_Accuracy": "accuracy_overall_default",
        "pmp_LLC_Coverage": "coverage_llc_default",
        "pmp_L1D_Coverage": "coverage_l1d_default",
        "pmp_L2C_Coverage": "coverage_l2c_default",
        "pmp_L1D_Accuracy": "accuracy_l1d_default",
        "pmp_L2C_Accuracy": "accuracy_l2c_default",
    }

    # Only apply renames for columns that actually exist in the loaded CSV
    rename_dict_default = {
        k: v for k, v in potential_renames.items() if k in default_df.columns
    }
    default_df = default_df.rename(columns=rename_dict_default)

    # Load and process the current run's dataframe (adaptive PMP)
    adaptive_df = current_df.rename(
        columns={
            "ipc_pmp": "ipc_adaptive",
            "pmp_Speedup": "speedup_adaptive",
            "pmp_Overall_Accuracy": "accuracy_overall_adaptive",
            "pmp_LLC_Coverage": "coverage_llc_adaptive",
            "pmp_L1D_Coverage": "coverage_l1d_adaptive",
            "pmp_L2C_Coverage": "coverage_l2c_adaptive",
            "pmp_L1D_Accuracy": "accuracy_l1d_adaptive",
            "pmp_L2C_Accuracy": "accuracy_l2c_adaptive",
        }
    )

    # Identify which columns are available to merge
    potential_merge_cols = [
        "ipc_default",
        "speedup_default",
        "accuracy_overall_default",
        "coverage_llc_default",
        "coverage_l1d_default",
        "coverage_l2c_default",
        "accuracy_l1d_default",
        "accuracy_l2c_default",
    ]

    # Filter cols_to_merge to only those present in default_df
    cols_to_merge = ["workload"] + [
        c for c in potential_merge_cols if c in default_df.columns
    ]

    # Merge dataframes
    merged_df = pd.merge(
        adaptive_df, default_df[cols_to_merge], on="workload", how="inner"
    )

    if merged_df.empty:
        print(
            "Warning: No common workloads found between current and comparison data. Skipping comparison.",
            file=sys.stderr,
        )
        return

    # Save merged data to a new CSV
    comparison_csv_path = os.path.join(output_dir, "pmp_comparison_per_workload.csv")
    merged_df.to_csv(comparison_csv_path, index=False, float_format="%.4f")
    print(f"Saved comparison metrics to {comparison_csv_path}")

    # Generate comparison graphs
    generate_comparison_graphs(merged_df, output_dir)


def create_output_directory():
    """Creates a timestamped directory for the results at the project root."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dir_name = f"pmp_results_{timestamp}"
    try:
        # Assumes this script is in scripts/draw, so ../../ is the project root
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        output_dir = os.path.join(project_root, "results", dir_name)
        os.makedirs(output_dir, exist_ok=True)
        print(f"Results will be saved in: {output_dir}")
        return output_dir
    except Exception as e:
        print(f"Error creating output directory: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate PMP evaluation reports and graphs."
    )
    parser.add_argument(
        "--compare",
        metavar="PATH",
        help="Path to a previous result directory to compare against.",
    )
    parser.add_argument(
        "--cores",
        type=int,
        default=1,
        choices=[1, 2, 4, 8],
        help="Number of cores used in the simulation (1, 2, 4, or 8). Default is 1.",
    )
    args = parser.parse_args()

    output_directory = create_output_directory()
    if not output_directory:
        sys.exit(1)

    df_detail, df_summary = generate_reports(output_directory, args.cores)

    if df_detail is not None and df_summary is not None:
        generate_graphs(df_detail, df_summary, output_directory)
    else:
        print(
            "Could not generate graphs because data generation failed.", file=sys.stderr
        )

    # If a comparison directory is provided, run the comparison
    if args.compare:
        if df_detail is not None:
            generate_comparison_report(df_detail, args.compare, output_directory)
        else:
            print(
                "Could not generate comparison report because initial data generation failed.",
                file=sys.stderr,
            )

    print("\n--- PMP Report Generation Complete ---")
