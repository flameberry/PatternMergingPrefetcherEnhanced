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
OUTPUT_CHART_ACCURACY_COVERAGE = 'pmp_accuracy_coverage_summary.png' # New
OUTPUT_CHART_USEFUL_USELESS = 'pmp_useful_useless_summary.png' # New
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
        
    if 'pmp_Speedup' not in df.columns or 'workload' not in df.columns:
        print(f"Warning: {csv_file} is missing 'pmp_Speedup' or 'workload' column. Skipping speedup bar chart.")
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

    if 'pmp_Overall_Accuracy' not in df or 'pmp_Speedup' not in df:
        print(f"Warning: {csv_file} missing required columns ('pmp_Overall_Accuracy' or 'pmp_Speedup'). Skipping scatter plot.")
        return

    plt.figure(figsize=(10, 8))
    
    plt.scatter(df['pmp_Overall_Accuracy'], df['pmp_Speedup'], alpha=0.7, edgecolors='w')
    
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

def plot_accuracy_coverage_summary(csv_file, output_image):
    """
    Creates a bar chart of overall accuracy and coverage metrics,
    inspired by Figure 9.
    """
    try:
        df = pd.read_csv(csv_file).iloc[0]
    except (FileNotFoundError, IndexError):
        print(f"Error: Could not find {csv_file} or it is empty", file=sys.stderr)
        return

    try:
        metrics = {
            'LLC Coverage': df['pmp_Mean_LLC_Coverage'],
            'L1D Accuracy': df['pmp_Mean_L1D_Accuracy'],
            'L2C Accuracy': df['pmp_Mean_L2C_Accuracy']
        }
    except KeyError:
        print(f"Error: CSV {csv_file} is missing required columns for Accuracy/Coverage plot.", file=sys.stderr)
        return

    labels = list(metrics.keys())
    values = list(metrics.values())
    
    plt.figure(figsize=(10, 6))
    
    bars = plt.bar(labels, values, color=['#007acc', '#cc3300', '#009966'])
    
    plt.title('Overall Coverage and Accuracy', fontsize=16, fontweight='bold')
    plt.ylabel('Rate', fontsize=12)
    
    # Format Y axis as percentage
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.ylim(0, 1.0)
    
    # Add data labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, f'{yval:.1%}', 
                 ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.grid(axis='y', linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Accuracy/Coverage summary chart saved to {output_image}")


def plot_useful_useless_summary(csv_file, output_image):
    """
    Creates a bar chart of mean useful/useless prefetches,
    inspired by Figure 10.
    """
    try:
        df = pd.read_csv(csv_file).iloc[0]
    except (FileNotFoundError, IndexError):
        print(f"Error: Could not find {csv_file} or it is empty", file=sys.stderr)
        return

    try:
        metrics = {
            'L1D Useful': df['pmp_Mean_L1D_Useful'],
            'L1D Useless': df['pmp_Mean_L1D_Useless'],
            'L2C Useful': df['pmp_Mean_L2C_Useful'],
            'L2C Useless': df['pmp_Mean_L2C_Useless']
        }
    except KeyError:
        print(f"Error: CSV {csv_file} is missing required columns for Useful/Useless plot.", file=sys.stderr)
        return

    labels = list(metrics.keys())
    values = list(metrics.values())
    
    plt.figure(figsize=(12, 7))
    
    colors = ['#007acc', '#cc3300', '#009966', '#ff9900']
    bars = plt.bar(labels, values, color=colors)
    
    # Use a log scale for the Y-axis as in the example
    plt.yscale('log')
    plt.title('Average Useful and Useless Prefetches', fontsize=16, fontweight='bold')
    plt.ylabel('Number (Log Scale)', fontsize=12)
    
    # Add data labels
    for bar in bars:
        yval = bar.get_height()
        if yval > 0: # Only label non-zero bars
            plt.text(bar.get_x() + bar.get_width()/2.0, yval * 1.1, f'{yval:,.0f}', 
                     ha='center', va='bottom', fontsize=10)

    plt.grid(axis='y', linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"Useful/Useless summary chart saved to {output_image}")


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
    plot_accuracy_coverage_summary(CSV_OVERALL_SUMMARY, OUTPUT_CHART_ACCURACY_COVERAGE)
    plot_useful_useless_summary(CSV_OVERALL_SUMMARY, OUTPUT_CHART_USEFUL_USELESS)
    
    print("\nAll plots generated successfully.")


