import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from get_results import *
from draw_para import *

print('Using results from run_single_core_gaze_sensitivity.py and run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
prefetchers = ['no', 'vgaze', 'vgaze_sensitivity_rs8KB', 'vgaze_sensitivity_rs16KB', 'vgaze_sensitivity_rs32KB', 'vgaze_sensitivity_rs64KB'] #, 'vgaze_rs_128'
prefixes = {prefetcher: 'v00' for prefetcher in prefetchers}
labels = {'vgaze':'4KB', 'vgaze_sensitivity_rs8KB':'8KB', 'vgaze_sensitivity_rs16KB':'16KB', 'vgaze_sensitivity_rs32KB':'32KB', 'vgaze_sensitivity_rs64KB':'64KB', 'vgaze_rs_128':'128KB'}
colors = {'vgaze':'#000000', 'vgaze_sensitivity_rs8KB':'#3E3E3E', 'vgaze_sensitivity_rs16KB':'#6E6E6E', 'vgaze_sensitivity_rs32KB':'#9E9E9E', 'vgaze_sensitivity_rs64KB':'#CECECE', 'vgaze_rs_128':'#FEFEFE'}
workloads_name_map.update([('spec', 'avg_spec'), ('ligra', 'avg_ligra'), ('parsec', 'avg_parsec'), ('cloudsuites', 'avg_cloud')])

speedup_detail = get_singlecore_speedup_detail(prefetchers, prefixes, workloads_all)
speedup_spec = get_singlecore_speedup(prefetchers, prefixes, workloads_spec)
speedup_ligra = get_singlecore_speedup(prefetchers, prefixes, workloads_ligra)
speedup_parsec = get_singlecore_speedup(prefetchers, prefixes, workloads_parsec)

for prefetcher in prefetchers:
    speedup_detail[prefetcher]['spec'] = speedup_spec[prefetcher]
    speedup_detail[prefetcher]['ligra'] = speedup_ligra[prefetcher]
    speedup_detail[prefetcher]['parsec'] = speedup_parsec[prefetcher]
    
# -------------------------- drawing figure 18 --------------------------
fig, ax = plt.subplots(figsize=(3.7, 0.75))
prefetchers.remove('no') # not draw


ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.15, zorder=0)

annotate_x = []

bar_width = 0.15 
set_interval = 0.35

positions = np.asarray([(set_interval + bar_width * len(prefetchers)) * j for j in range(len(workloads_sensitivity))])+bar_width/2

for j, prefetcher in enumerate(prefetchers):
    bar_positions = (set_interval+bar_width)/2 + positions + j * bar_width
    d = [(speedup_detail[prefetcher][workload] / speedup_detail['vgaze'][workload]) for workload in workloads_sensitivity]
    bars = ax.bar(bar_positions, d, width=bar_width, label=labels[prefetcher], color=colors[prefetcher], edgecolor='black',linewidth=0.15, zorder=10, bottom=0)
    ax.bar(bar_positions, d, width=bar_width, facecolor=(0, 0, 0, 0), edgecolor="black", linewidth=0.15, zorder=100, bottom=0)
    if prefetcher == 'vgaze':
        annotate_x = bar_positions + 5.5 * bar_width
    if prefetcher == 'vgaze_sensitivity_rs32KB':
        annotate_y_bias = 0.055
    if prefetcher == 'vgaze_sensitivity_rs64KB':
        annotate_y_bias = 0.005
    for j, value in enumerate(d):
        if value > 1.1:  # Adjust this threshold as needed
            if prefetcher == 'vgaze_sensitivity_rs32KB':
                ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 1.1), xytext=(annotate_x[j], 1.1 + annotate_y_bias),
                        textcoords='data', ha='left', va='bottom', fontsize=4, color='black',
                        arrowprops=dict(arrowstyle='->', color='black', linewidth=0.3, shrinkA=0, shrinkB=0,
                                        connectionstyle='angle,rad=0.9,angleA=180,angleB=-90', mutation_scale=3))
            elif prefetcher == 'vgaze_sensitivity_rs64KB':
                ax.annotate(f'{value:.2f}', xy=(bar_positions[j], 1.1), xytext=(annotate_x[j], 1.1 + annotate_y_bias),
                        textcoords='data', ha='left', va='bottom', fontsize=4, color='black',
                        arrowprops=dict(arrowstyle='->', color='black', linewidth=0.3, shrinkA=0, shrinkB=0,
                                        connectionstyle='angle,rad=0.8,angleA=180,angleB=-90', mutation_scale=3))

        
print(positions)
interval_positions = positions + set_interval/2 + bar_width * 3 / 2
ax.set_xticks(interval_positions)
ax.tick_params(axis='y', length=1, labelsize=5, width=0.15, pad=1)

ax.set_xticklabels([workloads_name_map[workload] for workload in workloads_sensitivity], rotation=45, ha="right", rotation_mode='anchor')


ax.set_ylim(0.5, 1.1)
ax.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1])
ax.set_yticklabels(['0.50', '0.60', '0.70', '0.80', '0.90', '1.00', '1.10'])
ax.tick_params(axis='x', direction='out', length=2, width=0.15, labelsize=5, pad=1)
ax.margins(0.01)
ax.spines['bottom'].set_linewidth(0.15)
ax.spines['bottom'].set_zorder(50)
ax.spines['left'].set_linewidth(0.15)
ax.spines['top'].set_linewidth(0.15)
ax.spines['right'].set_linewidth(0.15)
ax.spines['top'].set_zorder(200)


led = fig.legend(loc='upper center', ncol=8, frameon=False, framealpha=1, edgecolor='black', fontsize=5, bbox_to_anchor=(0.55, 1.1))
for text in led.get_texts():
    if '4KB' in text.get_text() and '64KB' not in text.get_text():
        text.set_weight('bold') 
frame = led.get_frame()
frame.set_linewidth(0.15)

fig.text(0.05, 0.5, 'Speedup normalized to\nthe baseline config', va='center', ha='center', rotation='vertical', fontsize=5)

plt.savefig('fig/fig18.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)