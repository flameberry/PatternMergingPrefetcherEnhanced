import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from get_results import *
from draw_para import *

print('Using results from run_single_core_fig12.py')

# -------------------------- getting corresponding results --------------------------
prefetchers = ['no', 'vberti', 'pmp', 'gaze']
prefixes = {prefetcher: 'v00' for prefetcher in prefetchers}

speedup_qmm_server = get_singlecore_speedup(prefetchers, prefixes, workloads_qmm_server)
speedup_qmm_client = get_singlecore_speedup(prefetchers, prefixes, workloads_qmm_client)
speedup_gap = get_singlecore_speedup(prefetchers, prefixes, workloads_gap)
speedup_detail = get_singlecore_speedup_detail(prefetchers, prefixes, workloads_qmm_gap)
# add averages
speedup_detail['gaze']['gap'], speedup_detail['gaze']['qmm_server'], speedup_detail['gaze']['qmm_client'] = speedup_gap['gaze'], speedup_qmm_server['gaze'], speedup_qmm_client['gaze']
speedup_detail['vberti']['gap'], speedup_detail['vberti']['qmm_server'], speedup_detail['vberti']['qmm_client'] = speedup_gap['vberti'], speedup_qmm_server['vberti'], speedup_qmm_client['vberti']
speedup_detail['pmp']['gap'], speedup_detail['pmp']['qmm_server'], speedup_detail['pmp']['qmm_client'] = speedup_gap['pmp'], speedup_qmm_server['pmp'], speedup_qmm_client['pmp']

# -------------------------- drawing figure 12 --------------------------
fig, axs = plt.subplots(1, 2, figsize=(3.7, 0.8))
prefetchers.remove('no') # not draw

for i, ax in enumerate(axs):
    ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.15, zorder=0)
    annotate_x = []

    if i == 0:
        ax.text(0.01, 0.96, "(a) GAP", transform=ax.transAxes, fontsize=6, va='top', ha='left')
        workloads = workloads_fig12_gap
        bar_width = 0.15 
        set_interval = 0.35

        positions = np.asarray([(set_interval + bar_width * len(prefetchers)) * j for j in range(len(workloads))])+bar_width/2

        for j, prefetcher in enumerate(prefetchers):
            bar_positions = (set_interval+bar_width)/2 + positions + j * bar_width
            d = [speedup_detail[prefetcher][workload[0]] for workload in workloads]
            bars = ax.bar(bar_positions, d, width=bar_width, label=prefetcher_dict[prefetcher], color=color_dict[prefetcher], edgecolor='black',linewidth=0.15, zorder=10, bottom=0)
            ax.bar(bar_positions, d, width=bar_width, facecolor=(0, 0, 0, 0), edgecolor="black", linewidth=0.15, zorder=100, bottom=0)

                
        print(positions)
        interval_positions = positions + set_interval/2 + bar_width * 3 / 2
        ax.set_xticks(interval_positions)
        ax.tick_params(axis='y', length=1, labelsize=5, width=0.15, pad=1)
        ax.set_xticklabels([workload[1] for workload in workloads], rotation=45, ha="right", rotation_mode='anchor')

        
        ax.set_ylim(0.8, 3.3)
        ax.set_yticks([1, 1.5, 2, 2.5, 3])
        ax.set_yticklabels(['1.00', '1.50', '2.00', '2.50', '3.00'])
        # ax.tick_params(axis='x', length=0)
        ax.tick_params(axis='x', direction='out', length=1, width=0.15, labelsize=5, pad=1)

        ax.margins(0.01)
        ax.spines['bottom'].set_linewidth(0.15)
        ax.spines['bottom'].set_zorder(50)
        ax.spines['left'].set_linewidth(0.15)
        ax.spines['top'].set_linewidth(0.15)
        ax.spines['right'].set_linewidth(0.15)
        ax.spines['top'].set_zorder(200)

            
            
    elif i == 1:
        ax.text(0.01, 0.96, "(b) QMM", transform=ax.transAxes, fontsize=6, va='top', ha='left')
        workloads = workloads_fig12_qmm
        bar_width = 0.15 
        set_interval = 0.35

        positions = np.asarray([(set_interval + bar_width * len(prefetchers)) * (j if j<client_begin_idx else j+1) for j in range(len(workloads))])+bar_width/2

        for j, prefetcher in enumerate(prefetchers):
            bar_positions = (set_interval+bar_width)/2 + positions + (j if j<client_begin_idx else j+1) * bar_width
            d = [speedup_detail[prefetcher][workload[0]] for workload in workloads]
            bars = ax.bar(bar_positions, d, width=bar_width, label=prefetcher_dict[prefetcher], color=color_dict[prefetcher], edgecolor='black',linewidth=0.15, zorder=10, bottom=0)
            ax.bar(bar_positions, d, width=bar_width, facecolor=(0, 0, 0, 0), edgecolor="black", linewidth=0.15, zorder=100, bottom=0)

                
        print(positions)
        interval_positions = positions + set_interval/2 + bar_width * 3 / 2
        ax.set_xticks(interval_positions)
        ax.tick_params(axis='y', length=1, labelsize=5, width=0.15, pad=1)
        ax.set_xticklabels([workload[1] for workload in workloads], rotation=45, ha="right", rotation_mode='anchor')

        
        ax.set_ylim(0.8, 1.6)
        ax.set_yticks([0.80, 1.00, 1.20, 1.40, 1.60])
        ax.set_yticklabels(['0.80', '1.00', '1.20', '1.40', '1.60'])
        ax.tick_params(axis='x', direction='out', length=1, width=0.15, labelsize=5, pad=1)

        ax.margins(0.01)
        ax.spines['bottom'].set_linewidth(0.15)
        ax.spines['bottom'].set_zorder(50)
        ax.spines['left'].set_linewidth(0.15)
        ax.spines['top'].set_linewidth(0.15)
        ax.spines['right'].set_linewidth(0.15)
        ax.spines['top'].set_zorder(200)

        xmin_first = positions[0] - bar_width 
        xmax_first = positions[client_begin_idx - 1] + set_interval + bar_width + bar_width * len(prefetchers)  
        ax.axvspan(xmin_first, xmax_first, facecolor='lightgray', alpha=0.6, zorder=0) 
        m, h = (xmin_first+xmax_first)/2, 1.32
        # ax.annotate('Server', xy=(m, h), xytext=(0, 3), textcoords='offset points', ha='center', fontsize=5)

        # Second category background  
        xmin_second = positions[client_begin_idx] - bar_width  
        xmax_second = positions[-1] + set_interval + bar_width + bar_width * len(prefetchers)  
        ax.axvspan(xmin_second, xmax_second, facecolor='lightgray', alpha=0.6, zorder=0)
        m, h = (xmin_second+xmax_second)/2, 1.32 
        # ax.annotate('Client', xy=(m, h), xytext=(0, 3), textcoords='offset points', ha='center', fontsize=5)

# leg = ax.legend(bbox_to_anchor=(0.5, 0.5), loc='center left', markerscale=1.2, borderaxespad=0.8, fontsize=4.5, frameon=False, edgecolor='black')
handles, labels = axs[0].get_legend_handles_labels()  
# fig.legend(handles, labels, loc='upper center', fontsize=5, frameon=False, edgecolor='black', ncol=3)   
fig.legend(handles, labels, loc='upper center', fontsize=6, frameon=False, edgecolor='black', ncol=3, bbox_to_anchor=(0.5, 1.15))  

fig.text(0.04, 0.5, 'Speedup over\nno prefetching', va='center', ha='center', rotation='vertical', fontsize=6)

plt.savefig('fig/fig12.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)