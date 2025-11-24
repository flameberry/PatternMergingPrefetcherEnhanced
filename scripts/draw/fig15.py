import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from get_results import *
from draw_para import *

print('Using results from run_multi_core_hete.py and run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
prefetchers = ['no', 'vberti', 'pmp', 'gaze'] # , 'bingo'
prefixes = {prefetcher: 'v00' for prefetcher in prefetchers}
mix_type = 'hete'
speedup_detail = get_multicore_speedup_detail(4, prefetchers, prefixes, workloads_all, mix_type)

speedup_4core_detail = {}

for mix, workload in workloads_all_4core_heterogeneous_fig15:
    speedup_4core_detail[mix] = {}
    for i, core in enumerate(['core0', 'core1', 'core2', 'core3']):
        speedup_4core_detail[mix][core] = {}
        for prefetcher in prefetchers:
            speedup_4core_detail[mix][core][prefetcher] = speedup_detail[prefetcher][workload][i]

# -------------------------- drawing figure 15 --------------------------
fig, ax = plt.subplots(figsize=(3.75, 0.8))  
prefetchers.remove('no') # not draw
bar_width = 0.1  
set_interval = 0.2
# Create a background for Ligra workloads  

mixes = ['mix1', 'mix2', 'mix3', 'mix4', 'mix5']
cores = ['core0', 'core1', 'core2', 'core3', 'avg']

# ligra_start_index = len(workloads_ss_effect) - 6 * 2  # Adjust based on Ligra workloads count  

# Calculate positions for bars  
positions = np.asarray([(set_interval + bar_width * len(prefetchers)) * j for j in range(len(mixes) * len(cores))]) + bar_width / 2  
for i in range(len(positions)):
    positions[i] += 0.5 * (i // len(cores))

for j, prefetcher in enumerate(prefetchers):  
    bar_positions = (set_interval + bar_width) / 2 + positions + j * bar_width  
    d = []
    for mix in mixes:
        for core in cores:
            if core != 'avg':
                d.append(speedup_4core_detail[mix][core][prefetcher])
            else:
                d.append(np.mean([speedup_4core_detail[mix][c][prefetcher] for c in cores[:-1]]))
    if prefetcher == 'vberti':
        annotate_x = bar_positions - bar_width / 2
    if prefetcher == 'vberti':
        annotate_y_bias = 0.12
    elif prefetcher == 'pmp':
        annotate_y_bias = 0.065
    elif prefetcher == 'gaze':
        annotate_y_bias = 0.005
    for j, value in enumerate(d):
        if value > 2.6:  # Adjust this threshold as needed
            if prefetcher == 'vberti':
                ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 2.6), xytext=(annotate_x[j], 2.6 + annotate_y_bias),
                        textcoords='data', ha='left', va='bottom', fontsize=4, color='black',
                        arrowprops=dict(arrowstyle='->', color='black', linewidth=0.3, shrinkA=0, shrinkB=0,
                                        connectionstyle='angle,rad=1,angleA=180,angleB=-90', mutation_scale=3))
            elif prefetcher == 'pmp':
                ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 2.6), xytext=(annotate_x[j], 2.6 + annotate_y_bias),
                        textcoords='data', ha='left', va='bottom', fontsize=4, color='black',
                        arrowprops=dict(arrowstyle='->', color='black', linewidth=0.3, shrinkA=0, shrinkB=0,
                                        connectionstyle='angle,rad=0.9,angleA=180,angleB=-90', mutation_scale=3))
            elif prefetcher == 'gaze':
                ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 2.6), xytext=(annotate_x[j], 2.6 + annotate_y_bias),
                        textcoords='data', ha='left', va='bottom', fontsize=4, color='black',
                        )
    # Create bars  
    ax.bar(bar_positions, d, width=bar_width, label=prefetcher_dict[prefetcher], color=color_dict[prefetcher], edgecolor='black', linewidth=0.15, zorder=10)  

for i in range(len(mixes)):
    xmin = positions[i * len(cores) + len(cores) - 1]
    xmax = positions[i * len(cores)] + len(cores) * (set_interval + len(prefetchers) * bar_width) #+ bar_width * len(prefetchers)  
    ax.axvspan(xmin, xmax, facecolor='lightgray', alpha=0.6, zorder=0) 

# Add mixture labels under the bar groups  

for i, mix in enumerate(mixes):  
    # Calculate the center position for the mixture  
    mix_center =positions[i * len(cores)] + (len(cores) * (set_interval + bar_width * len(prefetchers))) / 2 
    ax.text(mix_center, 0.18, mix, ha='center', va='top', fontsize=5)  

# Add dashed vertical lines to separate mixtures  
for i in range(1, len(mixes)):  
    # Position to draw the line is at the start of the next mixture  
    line_x = positions[i * len(cores)] - 0.25
    ax.axvline(x=line_x, color='black', linestyle='--', linewidth=0.5, zorder=5)  

# Adjust x-ticks  
interval_positions = positions + set_interval / 2 + bar_width * 3 / 2  
ax.set_xticks(interval_positions)  
# ax.set_xticklabels([])  
ax.set_xticklabels(['c0', 'c1', 'c2', 'c3', 'avg'] * len(mixes))  

# Set y-axis limits and labels  
ax.set_ylim(0.5, 2.6)  
ax.set_xlim(left=interval_positions[0] - 3 * bar_width - set_interval, right=interval_positions[-1] + 3 * bar_width+ set_interval)
ax.set_yticks([0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5])  
ax.tick_params(axis='y', length=1, labelsize=5, width=0.15, pad=1)
ax.tick_params(axis='x', direction='out', length=1, width=0.15, labelsize=4, pad=1)
ax.set_yticklabels(['0.50', None, '1.00', None, '1.50', None, '2.00', None, '2.50'])  
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
led = fig.legend(handles, labels, loc='upper center', fontsize=5, frameon=True, framealpha=0, ncol=4, bbox_to_anchor=(0.5, 1.08))  
frame = led.get_frame()
frame.set_linewidth(0.15)
fig.text(0.04, 0.5, 'Speedup over\nno prefetching', va='center', ha='center', rotation='vertical', fontsize=6)
# Save the figure  
# plt.tight_layout()  
plt.savefig('fig/fig15.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)  
# plt.show() 