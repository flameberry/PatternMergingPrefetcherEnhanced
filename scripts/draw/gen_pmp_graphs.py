import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import matplotlib.ticker as mtick

# --- Configuration ---
CSV_PER_WORKLOAD = 'pmp_per_workload_metrics.csv'
CSV_OVERALL_SUMMARY = 'pmp_overall_summary.csv'

OUTPUT_CHART_SPEEDUP_BARH = 'pmp_speedup_per_workload.png'
OUTPUT_CHART_SPEEDUP_BOX = 'pmp_speedup_distribution.png'
OUTPUT_CHART_SCATTER = 'pmp_accuracy_vs_speedup.png'
OUTPUT_CHART_RADAR = 'pmp_overall_metrics_radar.png'
# --- End Configuration ---

def plot_speedup_barh(csv_file, output_image):
    """
    Creates a horizontal bar chart of speedup per workload.
    """
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}", file=sys.stderr)
        return

    if df.empty:
        print(f"Warning: {csv_file} is empty. Skipping speedup bar chart.")
        return

    df = df.sort_values(by='pmp_Speedup', ascending=True)
    
    plt.figure(figsize=(12, len(df) * 0.3 + 2)) # Dynamic height
    
    colors = ['#007acc' if x > 1.0 else '#cc3300' for x in df['pmp_Speedup']]
    bars = plt.barh(df['workload'], df['pmp_Speedup'], color=colors, align='center')
    
    plt.axvline(x=1.0, color='grey', linestyle='--', linewidth=1)
    
    plt.title('PMP Prefetcher Speedup per Workload', fontsize=16, fontweight='bold')
    plt.xlabel('Speedup (Higher is Better)', fontsize=12)
    plt.ylabel('Workload', fontsize=12)
    
    plt.yticks(fontsize=8)
    plt.xticks(fontsize=10)
    plt.grid(axis='x', linestyle=':', alpha=0.7)
    plt.tight_layout()
    
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    print(f"Horizontal speedup chart saved to {output_image}")
    plt.close()

def plot_speedup_distribution(csv_file, output_image):
    """
    Creates a box plot of the speedup distribution.
    """
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}", file=sys.stderr)
        return

    if 'pmp_Speedup' not in df or df['pmp_Speedup'].isnull().all():
        print(f"Warning: No valid speedup data in {csv_file}. Skipping distribution plot.")
        return

    plt.figure(figsize=(8, 6))
    
    plt.boxplot(df['pmp_Speedup'].dropna(), vert=False, patch_artist=True,
                boxprops=dict(facecolor='#007acc', alpha=0.7),
                medianprops=dict(color='yellow', linewidth=2),
                flierprops=dict(marker='o', markerfacecolor='red', markersize=8, alpha=0.5))
    
    plt.axvline(x=1.0, color='red', linestyle='--', linewidth=1)
    
    plt.title('Distribution of PMP Speedups', fontsize=16, fontweight='bold')
    plt.xlabel('Speedup', fontsize=12)
    plt.yticks([]) # Hide y-axis labels
    plt.grid(axis='x', linestyle=':', alpha=0.7)
    plt.tight_layout()
    
    plt.savefig(output_image, dpi=300)
    print(f"Speedup distribution box plot saved to {output_image}")
    plt.close()

def plot_accuracy_vs_speedup(csv_file, output_image):
    """
    Creates a scatter plot of Accuracy vs. Speedup.
    """
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}", file=sys.stderr)
        return

    if 'pmp_Accuracy' not in df or 'pmp_Speedup' not in df:
        print(f"Warning: {csv_file} missing required columns. Skipping scatter plot.")
        return

    plt.figure(figsize=(10, 8))
    
    plt.scatter(df['pmp_Accuracy'], df['pmp_Speedup'], alpha=0.7, edgecolors='w')
    
    plt.axhline(y=1.0, color='grey', linestyle='--', linewidth=1)
    
    plt.title('Prefetcher Accuracy vs. Workload Speedup', fontsize=16, fontweight='bold')
    plt.xlabel('Per-Workload Accuracy', fontsize=12)
    plt.ylabel('Per-Workload Speedup', fontsize=12)
    
    # Format axes as percentages and multipliers
    plt.gca().xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    
    plt.savefig(output_image, dpi=300)
    print(f"Accuracy vs. Speedup scatter plot saved to {output_image}")
    plt.close()

def plot_radar_chart(csv_file, output_image):
    """
    Creates a radar chart of the overall summary metrics.
    """
    try:
        df = pd.read_csv(csv_file).iloc[0]
    except (FileNotFoundError, IndexError):
        print(f"Error: Could not find {csv_file} or it is empty", file=sys.stderr)
        return
        
    try:
        # Normalize speedup (e.g., 1.13 -> 0.13)
        speedup = df['pmp_GMean_Speedup'] - 1.0
        # Invert Late Ratio (so higher is better)
        late_ratio = 1.0 - df['pmp_Mean_Late_Ratio']
        
        metrics = {
            'Speedup': speedup,
            'LLC Coverage': df['pmp_Mean_LLC_Coverage'],
            'Accuracy': df['pmp_Mean_Accuracy'],
            'Timeliness': late_ratio
        }
    except KeyError:
        print(f"Error: CSV {csv_file} is missing required columns.", file=sys.stderr)
        return

    labels = list(metrics.keys())
    values = list(metrics.values())
    num_vars = len(labels)
    
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    values += values[:1] # Close the circle
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    ax.fill(angles, values, color='#007acc', alpha=0.25)
    ax.plot(angles, values, color='#007acc', linewidth=2)
    
    # Set y-axis ticks to be percentages
    ax.set_rlabel_position(0)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_ylim(0, max(values) * 1.1) # Set limit slightly above max value
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=12)
    
    # Add labels for values
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.text(angle, value + 0.05, f"{value:.1%}",
                horizontalalignment='center', size=12,
                fontweight='bold', color='black')

    plt.title('Overall PMP Prefetcher Profile', fontsize=16, fontweight='bold', y=1.1)
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Overall metrics radar chart saved to {output_image}")


# --- Main execution ---
if __name__ == "__main__":
    # Check for dependencies
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        print(f"Error: Missing dependency {e.name}. Please install it using 'pip install {e.name}'", file=sys.stderr)
        sys.exit(1)

    print("--- Generating All PMP Graphs ---")
    
    plot_speedup_barh(CSV_PER_WORKLOAD, OUTPUT_CHART_SPEEDUP_BARH)
    plot_speedup_distribution(CSV_PER_WORKLOAD, OUTPUT_CHART_SPEEDUP_BOX)
    plot_accuracy_vs_speedup(CSV_PER_WORKLOAD, OUTPUT_CHART_SCATTER)
    plot_radar_chart(CSV_OVERALL_SUMMARY, OUTPUT_CHART_RADAR)
    
    print("\nAll plots generated successfully.")

