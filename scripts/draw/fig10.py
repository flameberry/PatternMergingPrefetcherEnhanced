import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from get_results import *
from draw_para import *

print('Using results from run_single_core_gaze_analysis.py and run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
prefetchers = ['no', 'gaze_analysis_pht4ss', 'gaze_analysis_sm4ss', 'gaze']
prefixes = {prefetcher: 'v00' for prefetcher in prefetchers}

speedup_detail = get_singlecore_speedup_detail(prefetchers, prefixes, workloads_all)

# -------------------------- drawing figure 4 --------------------------
fig, ax = plt.subplots(figsize=(3.7, 0.8))  
prefetcher_dict.update({'gaze_analysis_pht4ss': 'PHT4SS', 'gaze_analysis_sm4ss': 'SM4SS', 'gaze': 'Gaze'})
color_dict['gaze_analysis_pht4ss'], color_dict['gaze_analysis_sm4ss'] = color_dict['vberti'], color_dict['pmp']
prefetchers.remove('no') # not draw
bar_width = 0.22   
set_interval = 0.3
# Create a background for Ligra workloads  
ligra_start_index = len(workloads_fig10) - 6 * 2  # Adjust based on Ligra workloads count  

# Calculate positions for bars  
positions = np.asarray([(set_interval + bar_width * len(prefetchers)) * (j if j<ligra_start_index else j+0.5) for j in range(len(workloads_fig10))]) + bar_width / 2  

for j, prefetcher in enumerate(prefetchers):  
    bar_positions = (set_interval + bar_width) / 2 + positions + j * bar_width  
    d = [speedup_detail[prefetcher][workload] for workload in workloads_fig10]  
    if prefetcher == 'gaze_analysis_pht4ss':
        annotate_x = bar_positions + 3.25 * bar_width
    if prefetcher == 'gaze_analysis_pht4ss':
        annotate_y_bias = 0.12
    elif prefetcher == 'gaze_analysis_sm4ss':
        annotate_y_bias = 0.065
    elif prefetcher == 'gaze':
        annotate_y_bias = 0.005
    for j, value in enumerate(d):
        if value > 1.75:  # Adjust this threshold as needed
            if prefetcher == 'gaze_analysis_pht4ss':
                ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 1.75), xytext=(annotate_x[j], 1.75 + annotate_y_bias),
                        textcoords='data', ha='left', va='bottom', fontsize=4, color='black',
                        arrowprops=dict(arrowstyle='->', color='black', linewidth=0.3, shrinkA=0, shrinkB=0,
                                        connectionstyle='angle,rad=1,angleA=180,angleB=-90', mutation_scale=3))
            elif prefetcher == 'gaze_analysis_sm4ss':
                ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 1.75), xytext=(annotate_x[j], 1.75 + annotate_y_bias),
                        textcoords='data', ha='left', va='bottom', fontsize=4, color='black',
                        arrowprops=dict(arrowstyle='->', color='black', linewidth=0.3, shrinkA=0, shrinkB=0,
                                        connectionstyle='angle,rad=0.9,angleA=180,angleB=-90', mutation_scale=3))
            elif prefetcher == 'gaze':
                ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 1.75), xytext=(annotate_x[j], 1.75 + annotate_y_bias),
                        textcoords='data', ha='left', va='bottom', fontsize=4, color='black',
                        arrowprops=dict(arrowstyle='->', color='black', linewidth=0.3, shrinkA=0, shrinkB=0,
                                        connectionstyle='angle,rad=0.8,angleA=180,angleB=-90', mutation_scale=3))
    # Create bars  
    ax.bar(bar_positions, d, width=bar_width, label=prefetcher_dict[prefetcher], color=color_dict[prefetcher], edgecolor='black', linewidth=0.15, zorder=10)  

for i in range(6):
    xmin = positions[ligra_start_index + i * 2] + set_interval / 4
    xmax = positions[ligra_start_index + i * 2] + 2 * (set_interval + len(prefetchers) * bar_width) - set_interval / 4 #+ bar_width * len(prefetchers)  
    ax.axvspan(xmin, xmax, facecolor='lightgray', alpha=0.6, zorder=0) 
# Adjust x-ticks  
interval_positions = positions + set_interval / 2 + bar_width * 3 / 2  
ax.set_xticks(interval_positions)  
ax.set_xticklabels([workloads_name_map[workload] for workload in workloads_fig10], rotation=45, ha="right", rotation_mode='anchor')  

# Set y-axis limits and labels  
ax.set_ylim(1, 1.75)  
ax.set_xlim(left=interval_positions[0] - 1.5 * bar_width - set_interval, right=interval_positions[-1] + 1.5 * bar_width+ set_interval)
ax.set_yticks([1, 1.25, 1.5, 1.75])  
ax.tick_params(axis='y', length=1, labelsize=5, width=0.15, pad=1)
ax.tick_params(axis='x', direction='out', length=1, width=0.15, labelsize=5, pad=1)
ax.set_yticklabels(['1.00', '1.25', '1.50', '1.75'])  
# Add grid and customize appearance  
ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.15, zorder=0)  
ax.spines['bottom'].set_linewidth(0.15)
ax.spines['bottom'].set_zorder(50)
ax.spines['left'].set_linewidth(0.15)
ax.spines['top'].set_linewidth(0.15)
ax.spines['right'].set_linewidth(0.15)
ax.spines['top'].set_zorder(200)

# Add legend  
handles, labels = ax.get_legend_handles_labels()  
led = fig.legend(handles, labels, loc='upper center', fontsize=5, frameon=True, framealpha=0, ncol=3, bbox_to_anchor=(0.6, 1.08))  
frame = led.get_frame()
frame.set_linewidth(0.15)
fig.text(0.04, 0.5, 'Speedup over\nno prefetching', va='center', ha='center', rotation='vertical', fontsize=6)
# Save the figure  

plt.savefig('fig/fig10.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)  
