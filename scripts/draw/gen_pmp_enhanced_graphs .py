import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import matplotlib.ticker as mtick

# --- Configuration ---
PREFETCHERS = ['pmp', 'pmp_enhanced']  # Add more prefetchers if needed
# --- End Configuration ---

def plot_speedup_barh(csv_file, output_image, prefetcher):
    df = pd.read_csv(csv_file)
    if df.empty:
        print(f"{csv_file} is empty. Skipping speedup bar chart.")
        return

    col_speedup = f'{prefetcher}_Speedup'
    if col_speedup not in df:
        print(f"{col_speedup} not found in {csv_file}. Skipping.")
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
    print(f"Horizontal speedup chart saved to {output_image}")
    plt.close()

def plot_speedup_distribution(csv_file, output_image, prefetcher):
    df = pd.read_csv(csv_file)
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
    print(f"Speedup distribution box plot saved to {output_image}")
    plt.close()

def plot_accuracy_vs_speedup(csv_file, output_image, prefetcher):
    df = pd.read_csv(csv_file)
    col_speedup = f'{prefetcher}_Speedup'
    col_accuracy = f'{prefetcher}_Overall_Accuracy'

    if col_speedup not in df or col_accuracy not in df:
        print(f"Required columns for {prefetcher} missing in {csv_file}. Skipping scatter plot.")
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
    print(f"Accuracy vs. Speedup scatter plot saved to {output_image}")
    plt.close()

def plot_radar_chart(csv_file, output_image, prefetcher):
    try:
        df = pd.read_csv(csv_file).iloc[0]
        speedup = df[f'{prefetcher}_GMean_Speedup'] - 1.0
        late_ratio = 1.0 - df[f'{prefetcher}_Mean_Late_Ratio']
        metrics = {
            'Speedup': speedup,
            'LLC Coverage': df[f'{prefetcher}_Mean_LLC_Coverage'],
            'Accuracy': df[f'{prefetcher}_Mean_Overall_Accuracy'],
            'Timeliness': late_ratio
        }
    except (KeyError, IndexError):
        print(f"Radar chart columns for {prefetcher} missing or CSV empty. Skipping radar chart.")
        return

    labels = list(metrics.keys())
    values = list(metrics.values())
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='#007acc', alpha=0.25)
    ax.plot(angles, values, color='#007acc', linewidth=2)
    ax.set_rlabel_position(0)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_ylim(0, max(values) * 1.1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=12)

    for angle, value in zip(angles[:-1], values[:-1]):
        ax.text(angle, value + 0.05, f"{value:.1%}",
                horizontalalignment='center', size=12,
                fontweight='bold', color='black')

    plt.title(f'Overall {prefetcher.upper()} Prefetcher Profile', fontsize=16, fontweight='bold', y=1.1)
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Overall metrics radar chart saved to {output_image}")


# --- Main execution ---
if __name__ == "__main__":
    print(f"--- Generating Graphs for Prefetchers: {', '.join(PREFETCHERS).upper()} ---")
    for prefetcher in PREFETCHERS:
        print(f"\n--- Processing {prefetcher.upper()} ---")
        csv_per_workload = f'{prefetcher}_per_workload_metrics.csv'
        csv_overall_summary = f'{prefetcher}_overall_summary.csv'

        plot_speedup_barh(csv_per_workload, f'{prefetcher}_speedup_per_workload.png', prefetcher)
        plot_speedup_distribution(csv_per_workload, f'{prefetcher}_speedup_distribution.png', prefetcher)
        plot_accuracy_vs_speedup(csv_per_workload, f'{prefetcher}_accuracy_vs_speedup.png', prefetcher)
        plot_radar_chart(csv_overall_summary, f'{prefetcher}_overall_metrics_radar.png', prefetcher)

    print("\nAll plots generated successfully for all prefetchers.")
