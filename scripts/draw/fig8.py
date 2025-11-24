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

coverage, late = {}, {}
for benchmark, workloads in benchmarks:
    coverage[benchmark], _ = get_singecore_coverage_accuracy(prefetchers, prefixes, workloads)
    late[benchmark] = get_late_ratio(prefetchers, prefixes, workloads)
print(late)
# -------------------------- drawing figure 8 --------------------------
fig, ax = plt.subplots(figsize=(3.9, 0.75))

ax.set_ylabel('Metric of Interest', fontsize=4, labelpad=2)
ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.15, zorder=0)
ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=1))

bar_width = 0.05
set_interval = 0.35
late_labelled = False
prefetchers.remove('no') # not draw

positions = np.asarray([(set_interval + bar_width * len(prefetchers)) * i for i in range(len(benchmarks))])+bar_width/2
for i, prefetcher in enumerate(prefetchers):
    bar_positions = (set_interval+bar_width)/2 + positions + i * bar_width
    d = [coverage[benchmark][prefetcher] for benchmark, _ in benchmarks]
    bars = ax.bar(bar_positions, d, width=bar_width, label=prefetcher_dict[prefetcher], color=color_dict[prefetcher], hatch=hatch_dict[prefetcher], edgecolor=edgecolor_dict[prefetcher],linewidth=0.15, zorder=10, bottom=0)
    ax.bar(bar_positions, d, width=bar_width, facecolor=(0, 0, 0, 0), edgecolor="black", linewidth=0.15, zorder=100, bottom=0)
    d = np.asarray(d) * np.asarray([late[benchmark][prefetcher] for benchmark, _ in benchmarks])
    if prefetcher == 'gaze' and not late_labelled:
        bars = ax.bar(bar_positions, d, width=bar_width, label='Late', color=color_dict['late'], edgecolor='black',linewidth=0.15, zorder=101, bottom=0)
        late_labelled = True
    else:
        bars = ax.bar(bar_positions, d, width=bar_width, label=None, color=color_dict['late'], edgecolor='black',linewidth=0.15, zorder=101, bottom=0)
    
    j=0
    for bar, bar_position in zip(bars, bar_positions):
        if(j==4):
            height = bar.get_height()
        j+=1

for i, (benchmark, _) in enumerate(benchmarks):
    set_positions = positions + (set_interval + bar_width *  len(prefetchers)) / 2
    ax.text(set_positions[i], -0.08, benchmark_dict[benchmark], horizontalalignment='center', verticalalignment='top', fontsize=5)

interval_positions = positions
ax.set_xticks(np.append(interval_positions, positions[-1] + positions[1] - positions[0] - bar_width / 2))
ax.tick_params(axis='x', direction='out', length=8, width=0.15)
ax.tick_params(axis='y', labelsize=4, width=0.15)
ax.set_xticklabels([])
ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
ax.set_ylim(0.0, 1)
ax.margins(0.01)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_linewidth(0.15)
ax.spines['left'].set_linewidth(0.15)

h, l = ax.get_legend_handles_labels()
kw = dict(ncol=9, loc="upper center", fontsize=4, edgecolor='black')    
leg1 = fig.legend(h[:9],l[:9], frameon=True, handlelength=1.5, handletextpad=0.2, labelspacing=0, framealpha=1, bbox_to_anchor=[0.47,1.1],**kw)
leg2 = fig.legend(h[9:],l[9:], frameon=False, handlelength=1.5, handletextpad=0.2, labelspacing=0, bbox_to_anchor=[0.47,0.98],**kw)
frame = leg1.get_frame()
frame.set_linewidth(0.15)
frame = leg2.get_frame()
frame.set_linewidth(0.15)
fig.add_artist(leg1)

for i, (benchmark, _) in enumerate(benchmarks):
    if benchmark == 'all':
        h, b, e = 0.8, positions[i] + set_interval/2 + 4 * bar_width, positions[i] + set_interval/2 + 6 * bar_width
        m = (b + e) / 2
        ax.axvspan(b, e, facecolor='lightgray', alpha=0.2)
        ax.annotate('$\it{f}$', xy=(m, h), xytext=(0, 3), textcoords='offset points', ha='center', fontsize=4)
        h, b, e = 0.8, positions[i] + set_interval/2 + 6 * bar_width, positions[i] + set_interval/2 + 8 * bar_width
        m = (b + e) / 2 
        ax.axvspan(b, e, facecolor='lightgray', alpha=0.6)
        ax.annotate('$\it{c}$', xy=(m, h), xytext=(0, 3), textcoords='offset points', ha='center', fontsize=4)
        

plt.savefig('fig/fig8.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)