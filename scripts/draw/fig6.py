import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from get_results import *
from draw_para import *

print('Using results from run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
benchmarks = [('spec06', workloads_spec06), ('spec17', workloads_spec17), 
              ('ligra', workloads_ligra), ('parsec', workloads_parsec), 
              ('cloudsuite', workloads_cloudsuite), ('all', workloads_all)]
prefetchers = ['no', 'ip_stride', 'spp_ppf', 'ipcp_l1', 'vberti', 'sms', 'bingo', 'dspatch', 'pmp', 'gaze']
prefixes = {prefetcher: 'v00' for prefetcher in prefetchers}

speedup = {}
for benchmark, workloads in benchmarks:
    speedup[benchmark] = get_singlecore_speedup(prefetchers, prefixes, workloads)


# -------------------------- drawing figure 6 --------------------------
fig, ax = plt.subplots(figsize=(8.3, 0.75))
prefetchers.remove('no') # not draw

ax.set_ylabel('Speedup over\nno prefectching', fontsize=5, labelpad=2)
ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.15, zorder=0)

bar_width = 0.1 
set_interval = 0.3

positions = np.asarray([(set_interval + bar_width * len(prefetchers)) * i for i in range(len(benchmarks))])+bar_width/2
for i, prefetcher in enumerate(prefetchers):
    bar_positions = (set_interval+bar_width)/2 + positions + i * bar_width
    d = [speedup[benchmark][prefetcher] for benchmark, _ in benchmarks]
    bars = ax.bar(bar_positions, d, width=bar_width, label=prefetcher_dict[prefetcher], color=color_dict[prefetcher], hatch=hatch_dict[prefetcher], edgecolor=edgecolor_dict[prefetcher],linewidth=0.15, zorder=10, bottom=0)
    ax.bar(bar_positions, d, width=bar_width, facecolor=(0, 0, 0, 0), edgecolor="black", linewidth=0.15, zorder=100, bottom=0)
    j=0
    for bar, bar_position in zip(bars, bar_positions):
        if(j==5):
            height = bar.get_height()
            ax.annotate(f'{round(height*100-100):02d}', xy=(bar_position, height), xytext=(0, 2), textcoords='offset points', ha='center', fontsize=3.5)
        j+=1

for i, (benchmark, _) in enumerate(benchmarks):
    set_positions = positions + (set_interval + bar_width *  len(prefetchers)) / 2
    ax.text(set_positions[i], 0.75, benchmark_dict[benchmark], horizontalalignment='center', verticalalignment='top', fontsize=5)

for i, (benchmark, _) in enumerate(benchmarks):
    if benchmark == 'all':
        h, b, e = 1.3, positions[i] + set_interval/2 + 4 * bar_width, positions[i] + set_interval/2 + 6 * bar_width
        m = (b + e) / 2
        ax.axvspan(b, e, facecolor='lightgray', alpha=0.2)
        ax.annotate('$\it{f}$', xy=(m, h), xytext=(0, 6), textcoords='offset points', ha='center', fontsize=4)
        h, b, e = 1.3, positions[i] + set_interval/2 + 6 * bar_width, positions[i] + set_interval/2 + 8 * bar_width
        m = (b + e) / 2 # #EC6568
        ax.axvspan(b, e, facecolor='lightgray', alpha=0.6)
        ax.annotate('$\it{c}$', xy=(m, h), xytext=(0, 6), textcoords='offset points', ha='center', fontsize=4)

print(positions)
interval_positions = positions
ax.set_xticks(np.append(interval_positions, positions[-1] + positions[1] - positions[0] - bar_width / 2))
ax.tick_params(axis='x', direction='out', length=10, width=0.15)
ax.tick_params(axis='y', labelsize=5, width=0.15)
ax.set_xticklabels([])
ax.set_yticks([0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
ax.set_ylim(0.8, 1.5)
ax.margins(0.01)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.axhline(y=1, color='black', linestyle='-', linewidth=0.6, zorder=0)
ax.spines['bottom'].set_linewidth(0.15)
ax.spines['bottom'].set_zorder(50)
ax.spines['left'].set_linewidth(0.15)

led = fig.legend(loc='upper center', ncol=9, frameon=True, framealpha=1, edgecolor='black', fontsize=5, bbox_to_anchor=(0.5, 1.1))
frame = led.get_frame()
frame.set_linewidth(0.15)

plt.savefig('fig/fig6.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)