import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from get_results import *
from draw_para import *

print('Using results from run_single_core_gaze_sensitivity.py and run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
prefetchers = [['no', 'gaze_sensitivity_rs512B', 'gaze_sensitivity_rs1KB', 'gaze_sensitivity_rs2KB', 'gaze'], ['no', 'gaze_sensitivity_pht128', 'gaze_sensitivity_pht256', 'gaze_sensitivity_pht512', 'gaze_sensitivity_pht1024']]
labels = [{'gaze_sensitivity_rs512B':'0.5KB', 'gaze_sensitivity_rs1KB':'1KB', 'gaze_sensitivity_rs2KB':'2KB', 'gaze': '4KB'}, {'gaze_sensitivity_pht128':'128', 'gaze_sensitivity_pht256':'256', 'gaze_sensitivity_pht512':'512', 'gaze_sensitivity_pht1024':'1024'}]
colors = [{'gaze_sensitivity_rs512B':'#AEAEAE', 'gaze_sensitivity_rs1KB':'#7E7E7E', 'gaze_sensitivity_rs2KB':'#4E4E4E', 'gaze':'#000000'}, {'gaze_sensitivity_pht128':'#AEAEAE', 'gaze_sensitivity_pht256':'#7E7E7E', 'gaze_sensitivity_pht512':'#4E4E4E', 'gaze_sensitivity_pht1024':'#000000'}]
workloads_name_map.update([('spec', 'avg_spec'), ('ligra', 'avg_ligra'), ('parsec', 'avg_parsec')])

fig, axs = plt.subplots(2, 1, figsize=(3.35, 1))

for i, ax in enumerate(axs):
    ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.15, zorder=0)
    
    # getting corresponding results
    prefixes = {prefetcher: 'v00' for prefetcher in prefetchers[i]}
    speedup_detail = get_singlecore_speedup_detail(prefetchers[i], prefixes, workloads_all)
    speedup_spec = get_singlecore_speedup(prefetchers[i], prefixes, workloads_spec)
    speedup_ligra = get_singlecore_speedup(prefetchers[i], prefixes, workloads_ligra)
    speedup_parsec = get_singlecore_speedup(prefetchers[i], prefixes, workloads_parsec)
    for prefetcher in prefetchers[i]:
        speedup_detail[prefetcher]['spec'] = speedup_spec[prefetcher]
        speedup_detail[prefetcher]['ligra'] = speedup_ligra[prefetcher]
        speedup_detail[prefetcher]['parsec'] = speedup_parsec[prefetcher]

    prefetchers[i].remove('no') # not draw
    annotate_x = []

    bar_width = 0.15 
    set_interval = 0.35

    positions = np.asarray([(set_interval + bar_width * len(prefetchers[i])) * j for j in range(len(workloads_sensitivity))])+bar_width/2

    for j, prefetcher in enumerate(prefetchers[i]):
        bar_positions = (set_interval+bar_width)/2 + positions + j * bar_width
        d = [(speedup_detail[prefetcher][workload] / speedup_detail['gaze' if i == 0 else 'gaze_sensitivity_pht1024'][workload]) for workload in workloads_sensitivity]
        bars = ax.bar(bar_positions, d, width=bar_width, label=labels[i][prefetcher], color=colors[i][prefetcher], edgecolor='black',linewidth=0.15, zorder=10, bottom=0)
        ax.bar(bar_positions, d, width=bar_width, facecolor=(0, 0, 0, 0), edgecolor="black", linewidth=0.15, zorder=100, bottom=0)

            
    print(positions)
    interval_positions = positions + set_interval/2 + bar_width * 3 / 2
    ax.set_xticks(interval_positions)
    ax.tick_params(axis='y', length=1, labelsize=5, width=0.15, pad=1)
    if i == 0:
        ax.set_xticklabels([])
    else:
        ax.set_xticklabels([workloads_name_map[workload] for workload in workloads_sensitivity], rotation=45, ha="right", rotation_mode='anchor')

    if i == 0:
        ax.set_ylim(0.6, 1.05)
        ax.set_yticks([0.60, 0.70, 0.80, 0.90, 1.00])
        ax.set_yticklabels(['0.60', '0.70', '0.80', '0.90', '1.00'])
        ax.tick_params(axis='x', length=0)
    else:
        ax.set_ylim(0.94, 1.03)
        ax.set_yticks([0.94, 0.96, 0.98, 1.00, 1.02])
        ax.tick_params(axis='x', direction='out', length=2, width=0.15, labelsize=5, pad=1)
    ax.margins(0.01)
    ax.spines['bottom'].set_linewidth(0.15)
    ax.spines['bottom'].set_zorder(50)
    ax.spines['left'].set_linewidth(0.15)
    ax.spines['top'].set_linewidth(0.15)
    ax.spines['right'].set_linewidth(0.15)
    ax.spines['top'].set_zorder(200)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    leg = ax.legend(bbox_to_anchor=(1.005, 0.5), loc='center left', markerscale=1.2, borderaxespad=0.8, fontsize=4.5, frameon=False, edgecolor='black')
    for text in leg.get_texts():
        if '4KB' in text.get_text() or '256' in text.get_text():
            text.set_weight('bold')  
    frame = leg.get_frame()
    frame.set_linewidth(0.15)
    if i == 0:
        ax.text(0.005, 1.13, "(a) Sensitivity to region size", transform=ax.transAxes, fontsize=6, va='top', ha='left')
    else:
        ax.text(0.005, 1.13, "(b) Sensitivity to PHT size", transform=ax.transAxes, fontsize=6, va='top', ha='left')


fig.text(0.04, 0.5, 'Speedup normalized to\nthe baseline config', va='center', ha='center', rotation='vertical', fontsize=5)

plt.savefig('fig/fig17.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)