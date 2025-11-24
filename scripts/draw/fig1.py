from get_results import *
from draw_para import *
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.ticker import AutoMinorLocator,MultipleLocator,FuncFormatter

print('Using results from run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
# no, 1offset, pmp, pc, dspatch, sms, bingo, gaze

prefetchers = ['no', '1offset', 'pmp', 'pc', 'dspatch', 'sms', 'bingo', 'gaze']
prefixes = {prefetcher: 'v00' for prefetcher in prefetchers}
speedup_spec17 = get_singlecore_speedup(prefetchers, prefixes, workloads_spec17)
speedup_cloud = get_singlecore_speedup(prefetchers, prefixes, workloads_cloudsuite)


# -------------------------- drawing figure 1 --------------------------
fig, ax = plt.subplots(figsize=(3.8, 1.5))

prefetchers = ['1offset', 'pmp', 'pc', 'dspatch', 'sms', 'bingo', 'gaze']


ax.set_xlabel('Speedup in '+r'$\it{CloudSuite}$'+' workloads', fontsize=7, labelpad=1.2)
ax.set_ylabel('Speedup in \n'+r'$\it{SPEC17}$'+' workloads', fontsize=7, labelpad=1.2)
ax.tick_params(axis='x', labelsize=6, width=0.5, pad=1, length=1)
ax.tick_params(axis='y', labelsize=6, width=0.5, pad=1, length=1)

ax.set_ylim(1.04, 1.35)
ax.set_xlim(0.945, 1.08)
ax.set_yticks([1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.35])
ax.set_xticks([0.96, 0.98, 1.00, 1.02, 1.04, 1.06, 1.08])
ax.set_xticklabels(['0.96', '0.98', r'$\bf{1.00}$', '1.02', '1.04', '1.06', '1.08'])

s = ax.scatter([speedup_cloud[prefetcher] for prefetcher in prefetchers[0:-1]], [speedup_spec17[prefetcher] for prefetcher in prefetchers[0:-1]], s=15, edgecolors='#000000', linewidths=0.4, color='#1e1e1e', zorder=10)
s = ax.scatter([speedup_cloud['gaze']], [speedup_spec17['gaze']], s=40, edgecolors='#000000', linewidths=0.4, color='#006833', marker='*', zorder=10)

ax.annotate('1offset', (speedup_cloud['1offset'], speedup_spec17['1offset']), textcoords="offset points", xytext=(8, -8), fontweight='bold', ha='center', fontsize=6)
ax.annotate('~3KB', (speedup_cloud['1offset'], speedup_spec17['1offset']), textcoords="offset points", xytext=(8, -8-6.5), ha='center', fontsize=6)

ax.annotate('Offset-opt', (speedup_cloud['pmp'], speedup_spec17['pmp']), textcoords="offset points", xytext=(0, 9), fontweight='bold', ha='center', fontsize=6)
ax.annotate('PMP, ~5KB', (speedup_cloud['pmp'], speedup_spec17['pmp']), textcoords="offset points", xytext=(0, 9-6.5), ha='center', fontsize=6)


ax.annotate('PC', (speedup_cloud['pc'], speedup_spec17['pc']), textcoords="offset points", xytext=(0, -8), fontweight='bold', ha='center', fontsize=6)
ax.annotate('~3KB', (speedup_cloud['pc'], speedup_spec17['pc']), textcoords="offset points", xytext=(0, -8-6.5), ha='center', fontsize=6)

ax.annotate('PC-opt', (speedup_cloud['dspatch'], speedup_spec17['dspatch']), textcoords="offset points", xytext=(0, 4+5), fontweight='bold', ha='center', fontsize=6)
ax.annotate('DSPatch, ~4KB', (speedup_cloud['dspatch'], speedup_spec17['dspatch']), textcoords="offset points", xytext=(0, 4), ha='center', fontsize=6)

ax.annotate('PC+Addr', (speedup_cloud['sms'], speedup_spec17['sms']), textcoords="offset points", xytext=(0, -7), fontweight='bold', ha='center', fontsize=6,)
ax.annotate('SMS, >100KB', (speedup_cloud['sms'], speedup_spec17['sms']), textcoords="offset points", xytext=(0, -7-6.5), ha='center', fontsize=6,)

ax.annotate('PC+Addr-opt', (speedup_cloud['bingo'], speedup_spec17['bingo']), xytext=(-35, -4), fontweight='bold', 
        textcoords='offset points', ha='center', fontsize=6, color='black',
        arrowprops=dict(arrowstyle='-', color='black', linewidth=0.3, shrinkA=0, shrinkB=0, mutation_scale=3, relpos=(0,0)))
ax.annotate('Bingo, >100KB', (speedup_cloud['bingo'], speedup_spec17['bingo']), textcoords="offset points", xytext=(-35, -4-6.5), ha='center', fontsize=6,)


ax.annotate('Gaze (this paper)', (speedup_cloud['gaze'], speedup_spec17['gaze']), textcoords="offset points", xytext=(-16, 5), ha='center', fontsize=6, fontweight='bold', color='#006833')
ax.annotate('~4.5KB', (speedup_cloud['gaze'], speedup_spec17['gaze']), textcoords="offset points", xytext=(-16, 5-6.5), ha='center', fontsize=6, fontweight='bold', color='#006833')


connections = [
    ('1offset', 'pmp', 'Pattern\nMerging', 0.007, -0.013),
    ('pc', 'dspatch', 'Dual Pattern', 0.01, -0.01),
    ('sms', 'bingo', 'Co-associating', 0.011, -0.02)
]

for prefetcher1, prefetcher2, label, xoff, yoff in connections:
    x1, y1 = speedup_cloud[prefetcher1], speedup_spec17[prefetcher1]
    x2, y2 = speedup_cloud[prefetcher2], speedup_spec17[prefetcher2]
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), zorder=0,
                arrowprops=dict(arrowstyle='->', color='gray', lw=0.6, linestyle='-',mutation_scale=7))
    ax.text((x1 + x2)/2 + xoff, (y1 + y2)/2 + yoff, label, fontsize=5, ha='center', va='center', color='gray')

ax.spines['bottom'].set_linewidth(0.5)
ax.spines['left'].set_linewidth(0.5)
ax.spines['right'].set_linewidth(0.5)
ax.spines['top'].set_linewidth(0.5)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)


plt.savefig('fig/fig1.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)
