import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.transforms import blended_transform_factory
from get_results import *
from draw_para import *

print('Using results from run_multi_core_hete.py, run_multi_core_homo.py, and run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
prefetchers = ['no', 'spp_ppf', 'vberti', 'bingo', 'dspatch', 'pmp', 'gaze']
prefixes = {prefetcher: 'v00' for prefetcher in prefetchers}

multi_core = {}
for core in [1, 2, 4, 8]:
    multi_core[str(core)] = {}
    
single_speedup = get_singlecore_speedup(prefetchers, prefixes, workloads_all)
for prefetcher in prefetchers:
    multi_core['1'][prefetcher] = {}
    multi_core['1'][prefetcher]['homo'], multi_core['1'][prefetcher]['hete'] = single_speedup[prefetcher], single_speedup[prefetcher]

for core in [2, 4, 8]:
    for mix in ['homo', 'hete']:
        speedup = get_multicore_speedup(core, prefetchers, prefixes, workloads_all, mix)
        for prefetcher in prefetchers:
            if prefetcher not in multi_core[str(core)]:
                multi_core[str(core)][prefetcher] = {}
            multi_core[str(core)][prefetcher][mix] = speedup[prefetcher]  
        
# -------------------------- drawing figure 14 --------------------------
fig, axs = plt.subplots(1, 2, figsize=(3.7, 1.35))
prefetchers.remove('no') # not draw
x = np.arange(len(prefetchers))

core_index = [1, 2, 3, 4]
for i, prefetcher in enumerate(prefetchers):
    ipc_values_homo = [multi_core[str(int(2**(index-1)))][prefetcher]['homo'] for index in core_index]
    ipc_values_hete = [multi_core[str(int(2**(index-1)))][prefetcher]['hete'] for index in core_index]
    alpha = 0.5 if prefetcher in ['ipcp_l1', 'spp_ppf', 'dspatch', 'pmp', 'vberti'] else 1
    linestyle = '--' if prefetcher in ['ipcp_l1', 'spp_ppf', 'dspatch', 'pmp', 'vberti'] else '-'
    axs[0].plot(core_index, ipc_values_homo, linestyle=linestyle, color=linecolor_dict[prefetcher], marker=marker_dict[prefetcher], label=prefetcher_dict[prefetcher], markersize=1.5, zorder=1, linewidth=0.5, alpha=alpha)
    axs[1].plot(core_index, ipc_values_hete, linestyle=linestyle, color=linecolor_dict[prefetcher], marker=marker_dict[prefetcher], label=None, markersize=1.5, zorder=1, linewidth=0.5, alpha=alpha)

axs[0].set_ylabel('Speedup over\nno prefetching', fontsize=5, labelpad=1.5)

axs[0].set_xlabel('')
axs[1].set_xlabel('')
fig.text(0.5, 0.04, 'Number of cores', ha='center', va='center', fontsize=6)


axs[0].set_title('(a)',x=0.5,y=0.93,fontsize=6)
axs[1].set_title('(b)',x=0.5,y=0.93,fontsize=6)
for ax in axs:

    ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.25, zorder=0)


    ax.set_xticks(core_index)
    ax.set_xticklabels([1, 2, 4, 8])
    ax.set_yticks([1, 1.05, 1.10, 1.15, 1.20, 1.25])
    ax.tick_params(axis='x', labelsize=4, pad=1, width=0.35, length=2)
    ax.tick_params(axis='y', labelsize=4, pad=1, width=0.35, length=2)

    ax.spines['bottom'].set_linewidth(0.35);
    ax.spines['left'].set_linewidth(0.35);
    ax.spines['right'].set_visible(False);
    ax.spines['top'].set_visible(False);
    ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.25, zorder=0)
    ax.spines['bottom'].set_zorder(50)

# fig.annotate(f'Number of cores', xy=(0.5, 0), xytext=(0.5, 0),
#         textcoords='data', ha='left', va='bottom', fontsize=4, color='black')
led = fig.legend(loc='upper center', ncol=6, frameon=True, framealpha=1, edgecolor='black', fontsize=4, bbox_to_anchor=(0.525, 1.02))
frame = led.get_frame()
frame.set_linewidth(0.15)

plt.tight_layout()
plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.2, hspace=None)
plt.savefig('fig/fig14.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)
