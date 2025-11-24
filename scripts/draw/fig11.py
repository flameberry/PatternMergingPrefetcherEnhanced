import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from get_results import *
from draw_para import *

print('Using results from run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
prefetchers = ['no', 'vberti', 'pmp', 'gaze']
prefixes = {prefetcher: 'v00' for prefetcher in prefetchers}

speedup = get_singlecore_speedup(prefetchers, prefixes, workloads_all)
speedup_spec17 = get_singlecore_speedup(prefetchers, prefixes, workloads_spec17)
speedup_cloud = get_singlecore_speedup(prefetchers, prefixes, workloads_cloudsuite)
speedup_detail = get_singlecore_speedup_detail(prefetchers, prefixes, workloads_all)
# add averages
speedup_detail['gaze']['all'], speedup_detail['gaze']['spec17'], speedup_detail['gaze']['cloud'] = speedup['gaze'], speedup_spec17['gaze'], speedup_cloud['gaze']
speedup_detail['vberti']['all'], speedup_detail['vberti']['spec17'], speedup_detail['vberti']['cloud'] = speedup['vberti'], speedup_spec17['vberti'], speedup_cloud['vberti']
speedup_detail['pmp']['all'], speedup_detail['pmp']['spec17'], speedup_detail['pmp']['cloud'] = speedup['pmp'], speedup_spec17['pmp'], speedup_cloud['pmp']

# -------------------------- drawing figure 11 --------------------------
fig, ax = plt.subplots(figsize=(8.3, 0.6))
prefetchers.remove('no') # not draw

ax.set_ylabel('Speedup over\nno prefectching', fontsize=5, labelpad=2)
ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.15, zorder=0)
workloads_name_map.update([('spec17', 'avg_spec17'), ('cloud', 'avg_cloud'),('all', 'avg_all')])
annotate_x = []

bar_width = 0.15 
set_interval = 0.35


positions = np.asarray([(set_interval + bar_width * len(prefetchers)) * i for i in range(len(workloads_fig11))])+bar_width/2
for i, prefetcher in enumerate(prefetchers):
    bar_positions = (set_interval+bar_width)/2 + positions + i * bar_width
    d = [speedup_detail[prefetcher][workload] for workload in workloads_fig11]
    bars = ax.bar(bar_positions, d, width=bar_width, label=prefetcher_dict[prefetcher], color=color_dict[prefetcher], edgecolor=edgecolor_dict[prefetcher],linewidth=0.15, zorder=10, bottom=0)
    ax.bar(bar_positions, d, width=bar_width, facecolor=(0, 0, 0, 0), edgecolor="black", linewidth=0.15, zorder=100, bottom=0)
    if prefetcher == 'vberti':
        annotate_x = bar_positions + 4 * bar_width
    if prefetcher == 'vberti':
        annotate_y_bias = 0.21
    elif prefetcher == 'pmp':
        annotate_y_bias = 0.11
    elif prefetcher == 'gaze':
        annotate_y_bias = 0.01
    for j, value in enumerate(d):
        if value > 1.6:  # Adjust this threshold as needed
            if prefetcher == 'vberti':
                ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 1.6), xytext=(annotate_x[j], 1.6 + annotate_y_bias),
                        textcoords='data', ha='left', va='bottom', fontsize=4, color='black',
                        arrowprops=dict(arrowstyle='->', color='black', linewidth=0.3, shrinkA=0, shrinkB=0,
                                        connectionstyle='angle,rad=1,angleA=180,angleB=-90', mutation_scale=3))
            elif prefetcher == 'pmp':
                ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 1.6), xytext=(annotate_x[j], 1.6 + annotate_y_bias),
                        textcoords='data', ha='left', va='bottom', fontsize=4, color='black',
                        arrowprops=dict(arrowstyle='->', color='black', linewidth=0.3, shrinkA=0, shrinkB=0,
                                        connectionstyle='angle,rad=0.9,angleA=180,angleB=-90', mutation_scale=3))
            elif prefetcher == 'gaze':
                ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 1.6), xytext=(annotate_x[j], 1.6 + annotate_y_bias),
                        textcoords='data', ha='left', va='bottom', fontsize=4, color='black',
                        arrowprops=dict(arrowstyle='->', color='black', linewidth=0.3, shrinkA=0, shrinkB=0,
                                        connectionstyle='angle,rad=0.7,angleA=180,angleB=-90', mutation_scale=3))
            # ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 1.6), xytext=(0, 1), textcoords='offset points', ha='center', va='bottom', fontsize=4)

b, e = positions[-3], positions[-1] + bar_width * 3 + set_interval
ax.axvspan(b, e, facecolor='lightgray', alpha=0.6, zorder=0)
        
print(positions)
interval_positions = positions + set_interval/2 + bar_width * 3 / 2
ax.set_xticks(interval_positions)
ax.tick_params(axis='x', direction='out', length=2, width=0.15, labelsize=4, pad=1)
ax.tick_params(axis='y', length=1, labelsize=5, width=0.15, pad=1)
ax.set_xticklabels([workloads_name_map[workload] for workload in workloads_fig11], rotation=45, ha="right", rotation_mode='anchor')
ax.set_yticks([0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6])
ax.set_yticklabels([None, 0.8, None, 1.0, None, 1.2, None, 1.4, None, 1.6])
ax.set_ylim(0.7, 1.6)
ax.margins(0.01)
ax.axhline(y=1, color='black', linestyle='-', linewidth=0.6, zorder=0)
ax.spines['bottom'].set_linewidth(0.15)
ax.spines['bottom'].set_zorder(50)
ax.spines['left'].set_linewidth(0.15)
ax.spines['top'].set_linewidth(0.15)
ax.spines['right'].set_linewidth(0.15)
ax.spines['top'].set_zorder(200)

led = fig.legend(loc='upper center', ncol=8, frameon=True, framealpha=1, edgecolor='black', fontsize=5, bbox_to_anchor=(0.5, 1.2))
frame = led.get_frame()
frame.set_linewidth(0.15)

plt.savefig('fig/fig11.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)