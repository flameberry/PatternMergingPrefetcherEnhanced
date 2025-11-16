import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import matplotlib.ticker as mtick

# --- Configuration ---
PREFETCHERS = ['pmp', 'pmp_enhanced']  # Add more prefetchers here

# Base filenames (they will be prefixed with the prefetcher name)
BASE_PER_WORKLOAD = '_per_workload_metrics.csv'
BASE_OVERALL_SUMMARY = '_overall_summary.csv'

OUTPUT_SUFFIXES = {
    'speedup_barh': '_speedup_per_workload.png',
    'speedup_box': '_speedup_distribution.png',
    'scatter': '_accuracy_vs_speedup.png',
    'accuracy_coverage': '_accuracy_coverage_summary.png',
    'useful_useless': '_useful_useless_summary.png'
}
# --- End Configuration ---


def plot_speedup_barh(csv_file, output_image, prefetcher):
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}", file=sys.stderr)
        return

    col_speedup = f'{prefetcher}_Speedup'
    if df.empty or 'workload' not in df.columns or col_speedup not in df.columns:
        print(f"Warning: Missing data in {csv_file}. Skipping speedup bar chart.")
        return

    df = df.sort_values(by=col_speedup, ascending=True)
    plt.figure(figsize=(12, len(df) * 0.3 + 2))
    colors = ['#007acc' if x > 1.0 else '#cc3300' for x in df[col_speedup]]
    plt.barh(df['workload'], df[col_speedup], color=colors, align='center')
    plt.axvline(x=1.0, color='grey', linestyle='--', linewidth=1)
    plt.title(f'{prefetcher.upper()} Prefetcher Speedup per Workload', fontsize=16, fontweight='bold')
    plt.xlabel('Speedup (Higher is Better)', fontsize=12)
    plt.ylabel('Workload', fontsize=12)
    plt.yticks(fontsize=8)
    plt.xticks(fontsize=10)
    plt.grid(axis='x', linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_image}")


def plot_speedup_distribution(csv_file, output_image, prefetcher):
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}", file=sys.stderr)
        return

    col_speedup = f'{prefetcher}_Speedup'
    if col_speedup not in df or df[col_speedup].isnull().all():
        print(f"No valid speedup data for {prefetcher} in {csv_file}. Skipping distribution plot.")
        return

    plt.figure(figsize=(8, 6))
    plt.boxplot(df[col_speedup].dropna(), vert=False, patch_artist=True,
                boxprops=dict(facecolor='#007acc', alpha=0.7),
                medianprops=dict(color='yellow', linewidth=2),
                flierprops=dict(marker='o', markerfacecolor='red', markersize=8, alpha=0.5))
    plt.axvline(x=1.0, color='red', linestyle='--', linewidth=1)
    plt.title(f'Distribution of {prefetcher.upper()} Speedups', fontsize=16, fontweight='bold')
    plt.xlabel('Speedup', fontsize=12)
    plt.yticks([])
    plt.grid(axis='x', linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved: {output_image}")


def plot_accuracy_vs_speedup(csv_file, output_image, prefetcher):
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}", file=sys.stderr)
        return

    col_speedup = f'{prefetcher}_Speedup'
    col_accuracy = f'{prefetcher}_Overall_Accuracy'
    if col_speedup not in df or col_accuracy not in df:
        print(f"Missing columns for {prefetcher} in {csv_file}. Skipping scatter plot.")
        return

    plt.figure(figsize=(10, 8))
    plt.scatter(df[col_accuracy], df[col_speedup], alpha=0.7, edgecolors='w')
    plt.axhline(y=1.0, color='grey', linestyle='--', linewidth=1)
    plt.title(f'{prefetcher.upper()} Accuracy vs. Workload Speedup', fontsize=16, fontweight='bold')
    plt.xlabel('Per-Workload Accuracy', fontsize=12)
    plt.ylabel('Per-Workload Speedup', fontsize=12)
    plt.gca().xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved: {output_image}")


def plot_accuracy_coverage_summary(csv_file, output_image, prefetcher):
    try:
        df = pd.read_csv(csv_file).iloc[0]
        metrics = {
            'LLC Coverage': df[f'{prefetcher}_Mean_LLC_Coverage'],
            'L1D Accuracy': df[f'{prefetcher}_Mean_L1D_Accuracy'],
            'L2C Accuracy': df[f'{prefetcher}_Mean_L2C_Accuracy']
        }
    except (FileNotFoundError, IndexError, KeyError):
        print(f"Skipping Accuracy/Coverage plot for {prefetcher}. Missing data.")
        return

    labels = list(metrics.keys())
    values = list(metrics.values())
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, values, color=['#007acc', '#cc3300', '#009966'])
    plt.title(f'{prefetcher.upper()} Overall Coverage and Accuracy', fontsize=16, fontweight='bold')
    plt.ylabel('Rate', fontsize=12)
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.ylim(0, 1.0)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, f'{yval:.1%}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    plt.grid(axis='y', linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved: {output_image}")


def plot_useful_useless_summary(csv_file, output_image, prefetcher):
    try:
        df = pd.read_csv(csv_file).iloc[0]
        metrics = {
            'L1D Useful': df[f'{prefetcher}_Mean_L1D_Useful'],
            'L1D Useless': df[f'{prefetcher}_Mean_L1D_Useless'],
            'L2C Useful': df[f'{prefetcher}_Mean_L2C_Useful'],
            'L2C Useless': df[f'{prefetcher}_Mean_L2C_Useless']
        }
    except (FileNotFoundError, IndexError, KeyError):
        print(f"Skipping Useful/Useless plot for {prefetcher}. Missing data.")
        return

    labels = list(metrics.keys())
    values = list(metrics.values())
    plt.figure(figsize=(12, 7))
    colors = ['#007acc', '#cc3300', '#009966', '#ff9900']
    bars = plt.bar(labels, values, color=colors)
    plt.yscale('log')
    plt.title(f'{prefetcher.upper()} Average Useful and Useless Prefetches', fontsize=16, fontweight='bold')
    plt.ylabel('Number (Log Scale)', fontsize=12)
    for bar in bars:
        yval = bar.get_height()
        if yval > 0:
            plt.text(bar.get_x() + bar.get_width()/2.0, yval * 1.1, f'{yval:,.0f}', ha='center', va='bottom', fontsize=10)
    plt.grid(axis='y', linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Saved: {output_image}")


# --- Main execution ---
if __name__ == "__main__":
    print(f"--- Generating Graphs for Prefetchers: {', '.join(PREFETCHERS).upper()} ---")
    for prefetcher in PREFETCHERS:
        print(f"\nProcessing {prefetcher.upper()}...")
        csv_per_workload = f'{prefetcher}{BASE_PER_WORKLOAD}'
        csv_overall_summary = f'{prefetcher}{BASE_OVERALL_SUMMARY}'

        plot_speedup_barh(csv_per_workload, f'{prefetcher}{OUTPUT_SUFFIXES["speedup_barh"]}', prefetcher)
        plot_speedup_distribution(csv_per_workload, f'{prefetcher}{OUTPUT_SUFFIXES["speedup_box"]}', prefetcher)
        plot_accuracy_vs_speedup(csv_per_workload, f'{prefetcher}{OUTPUT_SUFFIXES["scatter"]}', prefetcher)
        plot_accuracy_coverage_summary(csv_overall_summary, f'{prefetcher}{OUTPUT_SUFFIXES["accuracy_coverage"]}', prefetcher)
        plot_useful_useless_summary(csv_overall_summary, f'{prefetcher}{OUTPUT_SUFFIXES["useful_useless"]}', prefetcher)

    print("\nAll plots generated successfully for all prefetchers.")
