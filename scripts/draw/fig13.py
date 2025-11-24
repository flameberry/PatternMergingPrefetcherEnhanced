import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from get_results import *
from draw_para import *

print('Using results from run_single_core_multi_level.py and run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
multi_level_speedup = {}

prefetchers_g1_l1 = ['no', 'vberti', 'pmp', 'dspatch', 'ipcp_l1', 'gaze']
prefetchers_g1_l2 = [('spp_ppf', 'v31'), ('bingo', 'v32')]
for prefetcher_l2, prefix in prefetchers_g1_l2:
    prefixes = {prefetcher: prefix for prefetcher in prefetchers_g1_l1} # spp_ppf is v31, bingo is v32
    prefixes['no'] = 'v00'
    temp = get_singlecore_speedup(prefetchers_g1_l1, prefixes, workloads_all)
    for prefetcher_l1 in prefetchers_g1_l1:
        if prefetcher_l1 not in multi_level_speedup.keys():
            multi_level_speedup[prefetcher_l1] = {} 
        multi_level_speedup[prefetcher_l1][prefetcher_l2] = temp[prefetcher_l1]


prefetchers_g2_l1 = ['no', 'ip_stride']
prefetchers_g2_l2 = [('vberti', 'v33'), ('sms', 'v36'), ('bingo', 'v34'), ('dspatch', 'v37'), ('pmp', 'v35'), ('gaze', 'v38')]
for prefetcher_l2, prefix in prefetchers_g2_l2:
    prefixes = {prefetcher: prefix for prefetcher in prefetchers_g2_l1} # spp_ppf is v31, bingo is v32
    prefixes['no'] = 'v00'
    temp = get_singlecore_speedup(prefetchers_g2_l1, prefixes, workloads_all)
    for prefetcher_l1 in prefetchers_g2_l1:
        if prefetcher_l1 not in multi_level_speedup.keys():
            multi_level_speedup[prefetcher_l1] = {} 
        multi_level_speedup[prefetcher_l1][prefetcher_l2] = temp[prefetcher_l1]

# -------------------------- drawing figure 11 --------------------------
fig, ax = plt.subplots(figsize=(3.9, 0.75))
prefetchers_g1_l1.remove('no') # not draw
prefetchers_g2_l1.remove('no') # not draw

prefetchers_g1 = []
for prefetcher_l1 in prefetchers_g1_l1:
    for prefetcher_l2 in prefetchers_g1_l2:
        prefetchers_g1.append([prefetcher_l1, prefetcher_l2[0]])
        
prefetchers_g2 = []
for prefetcher_l1 in prefetchers_g2_l1:
    for prefetcher_l2 in prefetchers_g2_l2:
        prefetchers_g2.append([prefetcher_l1, prefetcher_l2[0]])
        
color_dict['dspatch'] = '#999999'
color_dict['pmp'] = '#cccccc'
# Set the width of the bars
bar_width = 0.2
set_interval = 1
begin_interval = 0.1

for i, prefetchers in enumerate(prefetchers_g1):
    bar_positions = begin_interval + i * bar_width
    d = multi_level_speedup[prefetchers[0]][prefetchers[1]]
    bars = ax.bar(bar_positions, d, width=bar_width, label=prefetcher_dict[prefetchers[0]]+'+'+prefetcher_dict[prefetchers[1]], color=color_dict[prefetchers[0]], hatch = '////\\\\\\\\' if prefetchers[1]=='bingo' else '++++' , edgecolor=edgecolor_dict[prefetchers[0]],linewidth=0.35, zorder=10, bottom=0)
    ax.bar(bar_positions, d, width=bar_width, facecolor=(0, 0, 0, 0), edgecolor="black", linewidth=0.35, zorder=100, bottom=0)

tick_positions = [begin_interval + bar_width * (len(prefetchers_g1) - 1) / 2, begin_interval + bar_width * len(prefetchers_g1) + set_interval + bar_width * (len(prefetchers_g2) - 1) / 2]
ax.set_xticks(tick_positions)
ax.set_xticklabels(['Group 1', 'Group 2'])

b, e = begin_interval + 0-bar_width, begin_interval + (len(prefetchers_g1)) * bar_width
m, h = (b+e)/2, 1.32
ax.axvspan(b, e, facecolor='lightgray', alpha=0.6, zorder=0)
ax.annotate('Group 1 (L1+L2)\n{vBerti, PMP, DSPatch, IPCP, Gaze}+{SPP-PPF, Bingo}', xy=(m, h), xytext=(0, 3), textcoords='offset points', ha='center', fontsize=4)

for i, prefetchers in enumerate(prefetchers_g2):
    bar_positions = begin_interval + i * bar_width + set_interval + bar_width * (len(prefetchers_g1))
    d = multi_level_speedup[prefetchers[0]][prefetchers[1]]
    bars = ax.bar(bar_positions, d, width=bar_width, label='+'+prefetcher_dict[prefetchers[1]], color=color_dict[prefetchers[1]], hatch=hatch_dict[prefetchers[1]], edgecolor=edgecolor_dict[prefetchers[1]],linewidth=0.35, zorder=10, bottom=0)
    ax.bar(bar_positions, d, width=bar_width, facecolor=(0, 0, 0, 0), edgecolor="black", linewidth=0.35, zorder=100, bottom=0)

b, e = begin_interval + set_interval + bar_width * (len(prefetchers_g1)) - bar_width, begin_interval + set_interval + bar_width * (len(prefetchers_g1)) + (len(prefetchers_g2)) * bar_width
m, h = (b+e)/2, 1.32
ax.axvspan(b, e, facecolor='lightgray', alpha=0.6, zorder=0)
ax.annotate('Group 2 (L1+L2)\nIP-stride+L2', xy=(m, h), xytext=(0, 3), textcoords='offset points', ha='center', fontsize=4)

ax.tick_params(axis='x', labelsize=4, width=0.35, length=2, pad=1)
ax.tick_params(axis='y', labelsize=4, width=0.35)
ax.set_ylim(1.0, 1.4)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

ax.set_ylabel('Norm. IPC', fontsize=5, labelpad=1)

ax.spines['bottom'].set_linewidth(0.35)
ax.spines['left'].set_linewidth(0.35)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['bottom'].set_zorder(50)
ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.25, zorder=0)
ax.tick_params(axis='y', pad=0)

h, l = ax.get_legend_handles_labels()
kw = dict(loc="upper center", fontsize=3, edgecolor='black')    
leg1 = fig.legend(h[:len(prefetchers_g1)],l[:len(prefetchers_g1)], ncol=5, handlelength=1.3, handletextpad=0.15, labelspacing=0, frameon=True, framealpha=1, bbox_to_anchor=[0.32 ,1.15],**kw)
leg2 = fig.legend(h[len(prefetchers_g1):],l[len(prefetchers_g1):], ncol=3, handlelength=1.3, handletextpad=0.15, labelspacing=0, frameon=True, bbox_to_anchor=[0.753,1.15],**kw)

frame = leg1.get_frame()
frame.set_linewidth(0.15)
frame = leg2.get_frame()
frame.set_linewidth(0.15)
fig.add_artist(leg1)

plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.4, hspace=None)
plt.savefig('fig/fig13.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)


