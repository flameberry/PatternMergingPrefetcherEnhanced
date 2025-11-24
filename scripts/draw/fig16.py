import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.transforms import blended_transform_factory
from get_results import *
from draw_para import *

print('Using results from run_single_core_system_sensitivity.py and run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
prefetchers = ['no', 'spp_ppf', 'vberti', 'bingo', 'dspatch', 'pmp', 'gaze'] # , 'bingo'

speedup_varying_dram, speedup_varying_llc_size, speedup_varying_l2c_size = {}, {}, {}

drams = [('800', 'v11'), ('1600', 'v12'), ('3200', 'v00'), ('6400', 'v13'), ('12800', 'v14')]
llcs = [('0.5', 'v24'), ('1', 'v21'), ('2', 'v00'), ('4', 'v22'), ('8', 'v23')]
l2cs = [('0.125', 'v25'), ('0.25', 'v26'), ('0.5', 'v00'), ('1', 'v27'), ('1.5', 'v28')]

for dram, prefix in drams:
    prefixes = {prefetcher: prefix for prefetcher in prefetchers}
    speedup_varying_dram[dram] = get_singlecore_speedup(prefetchers, prefixes, workloads_all)
for llc, prefix in llcs:
    prefixes = {prefetcher: prefix for prefetcher in prefetchers}
    speedup_varying_llc_size[llc] = get_singlecore_speedup(prefetchers, prefixes, workloads_all)
for l2c, prefix in l2cs:
    prefixes = {prefetcher: prefix for prefetcher in prefetchers}
    speedup_varying_l2c_size[l2c] = get_singlecore_speedup(prefetchers, prefixes, workloads_all)

# -------------------------- drawing figure 16 --------------------------
fig, axs = plt.subplots(1, 3, figsize=(3.7, 1.35))
prefetchers.remove('no') # not draw

# Figure 0
indices = [1, 2, 3, 4, 5]
dram_dict = {1:'800', 2:'1600', 3:'3200', 4:'6400', 5:'12800'}
llc_dict = {1:'0.5', 2:'1', 3:'2', 4:'4', 5:'8'}
l2c_dict = {1:'0.125', 2:'0.25', 3:'0.5', 4:'1', 5:'1.5'}

for i, prefetcher in enumerate(prefetchers):
    ipc_values = [speedup_varying_dram[dram_dict[index]][prefetcher] for index in indices]
    alpha = 0.5 if prefetcher in ['ipcp_l1', 'spp_ppf', 'dspatch'] else 1
    linestyle = '--' if prefetcher in ['ipcp_l1', 'spp_ppf', 'dspatch'] else '-'
    axs[0].plot(indices, ipc_values, linestyle=linestyle, color=linecolor_dict[prefetcher], marker=marker_dict[prefetcher], label=prefetcher_dict[prefetcher], markersize=1.5, zorder=1, linewidth=0.5, alpha=alpha)

for i, prefetcher in enumerate(prefetchers):
    ipc_values = [speedup_varying_llc_size[llc_dict[index]][prefetcher] for index in indices]
    alpha = 0.5 if prefetcher in ['ipcp_l1', 'spp_ppf', 'dspatch'] else 1
    linestyle = '--' if prefetcher in ['ipcp_l1', 'spp_ppf', 'dspatch'] else '-'
    axs[1].plot(indices, ipc_values, linestyle=linestyle, color=linecolor_dict[prefetcher], marker=marker_dict[prefetcher], label=None, markersize=1.5, zorder=1, linewidth=0.5, alpha=alpha)

for i, prefetcher in enumerate(prefetchers):
    ipc_values = [speedup_varying_l2c_size[l2c_dict[index]][prefetcher] for index in indices]
    alpha = 0.5 if prefetcher in ['ipcp_l1', 'spp_ppf', 'dspatch'] else 1
    linestyle = '--' if prefetcher in ['ipcp_l1', 'spp_ppf', 'dspatch'] else '-'
    axs[2].plot(indices, ipc_values, linestyle=linestyle, color=linecolor_dict[prefetcher], marker=marker_dict[prefetcher], label=None, markersize=1.5, zorder=1, linewidth=0.5, alpha=alpha)


for ax in axs:
    ax.tick_params(axis='x', labelsize=4, pad=1, width=0.35, length=2)
    ax.tick_params(axis='y', labelsize=4, pad=1, width=0.35, length=2)
    ax.set_xticks(indices)
    ax.set_yticks([1.1, 1.15, 1.2, 1.25, 1.3])
    ax.spines['bottom'].set_linewidth(0.35);
    ax.spines['left'].set_linewidth(0.35);
    ax.spines['right'].set_visible(False);
    ax.spines['top'].set_visible(False);
    ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.25, zorder=0)
    ax.spines['bottom'].set_zorder(50)

axs[0].set_yticklabels(['1.10', '1.15', '1.20', '1.25', '1.30'])
axs[1].set_yticklabels(['1.10', '1.15', '1.20', '1.25', '1.30'])
axs[2].set_yticklabels(['1.10', '1.15', '1.20', '1.25', '1.30'])
axs[1].set_ylabel('')
axs[2].set_ylabel('')

axs[0].set_xticklabels([800, 1600, 3200, 6400, 12800])
axs[0].set_xlabel('DRAM MTPS', fontsize=5, labelpad=1)
axs[0].set_ylabel('Speedup over\nno prefetching', fontsize=5, labelpad=1)
axs[0].set_title('(a)',x=0.5,y=0.93,fontsize=6)
x_start, x_end = len(prefetchers) - 3.2, len(prefetchers) - 2.8
axs[0].axvspan(x_start, x_end, facecolor='#FF4040', alpha=0.25)

axs[1].set_xticklabels([0.5, 1, 2, 4, 8])
axs[1].set_xlabel('LLC size per core (MB)', fontsize=5, labelpad=1)
axs[1].set_title('(b)',x=0.5,y=0.93,fontsize=6)
x_start, x_end = len(prefetchers) - 3.2, len(prefetchers) - 2.8
axs[1].axvspan(x_start, x_end, facecolor='#FF4040', alpha=0.25)

axs[2].set_xticklabels(['128', '256', '512', '1024', '1536'])
axs[2].set_xlabel('L2C size per core (KB)', fontsize=5, labelpad=1)
axs[2].set_title('(c)',x=0.5,y=0.93,fontsize=6)
x_start, x_end = len(prefetchers) - 3.2, len(prefetchers) - 2.8
axs[2].axvspan(x_start, x_end, facecolor='#FF4040', alpha=0.25)

led = fig.legend(loc='upper center', ncol=6, frameon=True, framealpha=1, edgecolor='black', fontsize=5, bbox_to_anchor=(0.525, 1.02))
frame = led.get_frame()
frame.set_linewidth(0.15)

# Show the plot
plt.tight_layout()
plt.subplots_adjust(hspace=0.1, wspace=0.2)
plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.2, hspace=None)
plt.savefig('fig/fig16.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)


