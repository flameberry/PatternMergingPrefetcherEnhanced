import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.transforms import blended_transform_factory
from scipy.stats import gmean
from get_results import *
from draw_para import *

print('Using results from run_single_core_gaze_analysis.py and run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
prefetchers = ['no', '1offset', 'gaze_analysis_pht', 'gaze']
prefixes = {prefetcher: 'v00' for prefetcher in prefetchers}

speedup_detail = get_singlecore_speedup_detail(prefetchers, prefixes, workloads_all)

# -------------------------- drawing figure 4 --------------------------
fig, ax = plt.subplots(figsize=(3.7, 1.5))
prefetchers.remove('no') # not draw
prefetcher_dict['1offset'], prefetcher_dict['gaze_analysis_pht'], prefetcher_dict['gaze']  = 'Offset', 'Gaze-PHT', 'Full Gaze'
linecolor_dict['1offset'], linecolor_dict['gaze_analysis_pht'], linecolor_dict['gaze'] = '#86b5a1', '#ac667e', '#e47159'

x = np.arange(len(prefetchers))
a = sorted(speedup_detail['gaze'].items(), key=lambda x: x[1])
sorted_workloads = [a[i][0] for i in range(len(a))]
# for i, w in enumerate(sorted_workloads):
#     print(i+1, w)
# print(a)

x_to_annotation = [1, 24, 32, 39, 79, 92, 113, 121, 142, 155, 163, 170, 185, 188, 192, 198, 201]

workload_index = [_+1 for _ in range(len(sorted_workloads))] 

for i, prefetcher in enumerate(prefetchers):
    ipc_values = [speedup_detail[prefetcher][workload] for workload in sorted_workloads]

    alpha = 1
    linestyle = '--' if prefetcher == 'gaze' else '-'
    zorder = 10 if prefetcher == 'gaze' else 20

    ax.plot(workload_index, ipc_values, linestyle=linestyle, color=linecolor_dict[prefetcher], marker=None, label=prefetcher_dict[prefetcher], markersize=1.5, zorder=zorder, linewidth=0.4, alpha=alpha)
    delta = 0
    if prefetcher == '1offset':
        delta = -0.025
    elif prefetcher == 'gaze_analysis_pht':
        delta = 0.025
    ax.annotate(f'{gmean(ipc_values):.2f}', xy=(201, ipc_values[-1]), xytext=(203, ipc_values[-1] + delta),
                        textcoords='data', ha='left', va='center', fontsize=3, color='black')
ax.annotate(f'AVG', xy=(201, ipc_values[-1]), xytext=(203, 2.7),
                    textcoords='data', ha='left', va='bottom', fontsize=3, color='black')

    
ipc_values = [max(speedup_detail['gaze'][workload], speedup_detail['1offset'][workload]) for workload in sorted_workloads]
i=0
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], 1), xytext=(x_to_annotation[i]+0.2, 1.2),
        textcoords='data', ha='left', va='center', fontsize=4, color='black', alpha=0.5, 
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=0.2', mutation_scale=3))
i=1
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i]+8, 1 + 0.4),
        textcoords='data', ha='right', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=-0.3', mutation_scale=3))
i=2
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i]+20, 1 + 0.6),
        textcoords='data', ha='right', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=0', mutation_scale=3))
i=3
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i]+9, 1 + 0.2),
        textcoords='data', ha='center', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=0', mutation_scale=3))
i=3+1
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i], 1 + 0.4),
        textcoords='data', ha='right', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=-0.3', mutation_scale=3))
i=4+1
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i], 1 + 0.6),
        textcoords='data', ha='right', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=-0.3', mutation_scale=3))
i=5+1
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i-1]+10, 1 + 0.4),
        textcoords='data', ha='center', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=-0.3', mutation_scale=3))
i=7
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i-1]+4, 1 + 0.6),
        textcoords='data', ha='center', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=0', mutation_scale=3))
i=6+1+1
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i]-10, 1 + 0.8),
        textcoords='data', ha='center', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=-0.3', mutation_scale=3))
i=7+1+1
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i]-18, 1 + 1),
        textcoords='data', ha='center', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=-0.3', mutation_scale=3))
i=8+1+1
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i-1]+12, 1 + 0.1),
        textcoords='data', ha='center', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=0', mutation_scale=3))
i=8+1+1+1
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i-1]+8, 1 + 0.9),
        textcoords='data', ha='center', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=0', mutation_scale=3))
i=9+1+1+1
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i]-5, 1 + 1.2),
        textcoords='data', ha='center', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=0', mutation_scale=3))
# i=10
# ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i], 1 + 1.4),
#         textcoords='data', ha='right', va='center', fontsize=4, color='black', alpha=0.5,
#         arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
#                         connectionstyle='arc3,rad=-0.3', mutation_scale=3))
# i=11
# ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i]-10, 1 + 1.45),
#         textcoords='data', ha='right', va='center', fontsize=4, color='black', alpha=0.5,
#         arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
#                         connectionstyle='arc3,rad=0', mutation_scale=3))
i=12+1+1+1
ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i]-10, 1 + 1.5),
        textcoords='data', ha='right', va='center', fontsize=4, color='black', alpha=0.5,
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
                        connectionstyle='arc3,rad=0', mutation_scale=3))
# i=15
# ax.annotate(workloads_name_map[sorted_workloads[x_to_annotation[i]-1]], xy=(x_to_annotation[i], ipc_values[x_to_annotation[i] - 1]), xytext=(x_to_annotation[i]-10, 1 + 1.6),
#         textcoords='data', ha='right', va='center', fontsize=4, color='black', alpha=0.5,
#         arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, alpha=0.5,
#                         connectionstyle='arc3,rad=0', mutation_scale=3))

ax.set_xlabel('Trace number', fontsize=5, labelpad=0.5)
ax.set_ylabel('Speedup over\nno prefetching', fontsize=5, labelpad=1.5)

ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.25, zorder=0)

N = 20 # Adjust N based on your preference
# ax.xaxis.set_major_locator(ticker.MultipleLocator(N))
# ax.set_xticks(workload_index)
# minor_locator = ticker.AutoMinorLocator()
# ax.xaxis.set_minor_locator(minor_locator)
ax.set_xlim(0.1,201.9)
ax.set_ylim(0.8, 2.7)
ax.axhline(y=1, color='#222222', linestyle='dashed', linewidth=0.25, alpha=0.8, zorder=0)
ax.set_yticks([0.9, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.7])
ax.set_yticklabels([0.9, None, None, 1.4, None, 1.8, None, 2.2, None, 2.6, None])
ax.set_xticks([1, 20, 40, 60, 80, 100, 120, 140, 160, 180, 201])
ax.set_xticklabels([1, 20, 40, 60, 80, 100, 120, 140, 160, 180, 201])

ax.tick_params(axis='x', which='minor', width=0.2, length=0.4)  
ax.tick_params(axis='x', labelsize=4, pad=1, width=0.2, length=1)
ax.tick_params(axis='y', labelsize=4, pad=1, width=0.2, length=2)


ax.spines['bottom'].set_linewidth(0.2);
ax.spines['left'].set_linewidth(0.2);
ax.spines['top'].set_linewidth(0.2);
ax.spines['right'].set_linewidth(0.2);
ax.grid(True, axis='y', linestyle='dashed', alpha=0.3, linewidth=0.25, zorder=0)
ax.spines['bottom'].set_zorder(50)

ax.legend(loc='best', ncol=6, frameon=False, fontsize=4)

plt.tight_layout()
plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.4, hspace=None)
plt.savefig('fig/fig9.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)
