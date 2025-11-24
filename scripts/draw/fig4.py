import matplotlib.pyplot as plt
import numpy as np
from get_results import *
from draw_para import *

print('Using results from run_single_core_fig4.py and run_single_core_main.py')

# -------------------------- getting corresponding results --------------------------
prefetchers = ['no', '1offset', '2offset', '3offset', '4offset']
prefixes = {prefetcher: 'v00' for prefetcher in prefetchers}
speedup = get_singlecore_speedup(prefetchers, prefixes, workloads_all)
llc_coverage, overall_accuracy = get_singecore_coverage_accuracy(prefetchers, prefixes, workloads_all)

# -------------------------- drawing figure 4 --------------------------
# Data for the example
offset_values = [1, 2, 3, 4]

coverage_ticks = [0.40, 0.45, 0.50, 0.55]
# Create a figure and a set of subplots with 1 row and 1 column
fig, ax1 = plt.subplots(figsize=(3.75, 1.25))

# Plot IPC on the first y-axis (left y-axis)
color1 = '#000000'
ax1.plot(offset_values, [speedup[f'{c}offset'] for c in offset_values], color=color1, marker='o', label='IPC', markersize=1.5, zorder=1, linewidth=0.75)
ax1.set_ylabel('Norm. IPC', color=color1, labelpad=2, fontsize=6)
ax1.tick_params(axis='y', labelcolor=color1, labelsize=4)
ax1.set_ylim(1.15, 1.21)

# Create a second y-axis on the right side (twin y-axis)
ax2 = ax1.twinx()

# Plot Accuracy on the second y-axis (right y-axis)
color2 = '#8D8D8D'
ax2.plot(offset_values, [overall_accuracy[f'{c}offset'] for c in offset_values], color=color2, marker='s', label='Accuracy', markersize=1.5, zorder=2, linewidth=0.75)
ax2.set_ylabel('Accuracy', color=color2, labelpad=2, fontsize=6)
ax2.tick_params(axis='y', labelcolor=color2, labelsize=4)
ax2.set_ylim(0.5, 1)

# Create a third y-axis on the left side (twin y-axis)
ax3 = ax1.twinx()
ax3.spines['right'].set_position(('outward', 27))  # Move the third y-axis to the right

# Plot Coverage on the third y-axis (left y-axis)
color3 = '#729ECD'
ax3.plot(offset_values, [llc_coverage[f'{c}offset'] for c in offset_values], color=color3, marker='^', label='Coverage', markersize=1.5, zorder=3, linewidth=0.75)
ax3.set_ylabel('Coverage', color=color3, labelpad=2, fontsize=6)  # Rotate and adjust label position
ax3.tick_params(axis='y', labelcolor=color3, labelsize=4)
ax3.set_ylim(0.4,0.55)
# ax3.set_yticks(coverage_ticks)

# Add legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
lines3, labels3 = ax3.get_legend_handles_labels()
# led = fig.legend(loc='upper center', ncol=6, frameon=True, framealpha=1, edgecolor='black', fontsize=4, bbox_to_anchor=(0.55, 1.02))
# frame = led.get_frame()
# frame.set_linewidth(0.15)
led = ax1.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='lower center', fontsize=3, frameon=True, framealpha=1, edgecolor='black')
frame = led.get_frame()
frame.set_linewidth(0.35)
ax1.set_xticks(offset_values)
ax1.tick_params(axis='x', labelsize=4)
rect = plt.Rectangle((1.9, ax1.get_ylim()[0] + 0.32*(ax1.get_ylim()[1] - ax1.get_ylim()[0])), 0.2, 0.66*(ax1.get_ylim()[1] - ax1.get_ylim()[0]),
                     linestyle='dashed', linewidth=0.5, edgecolor='#F15326', facecolor='none', zorder=0)
ax1.add_patch(rect)
# plt.xlabel('Offset Values')
ax1.set_xlabel('Number of used initial accesses', labelpad=2, fontsize=6)

label = '%.2f'%speedup['1offset']
ax1.annotate(label, (1, speedup['1offset']), textcoords="offset points", xytext=(0,3), ha='center', fontsize=4, color=color1)
label = '%.2f'%overall_accuracy['1offset']
ax2.annotate(label, (1, overall_accuracy['1offset']), textcoords="offset points", xytext=(7,-3), ha='center', fontsize=4, color=color2)
label = '%.2f'%llc_coverage['1offset']
ax3.annotate(label, (1, llc_coverage['1offset']), textcoords="offset points", xytext=(0,3), ha='center', fontsize=4, color=color3)


label = '%.2f'%speedup['2offset']
ax1.annotate(label, (2, speedup['2offset']), textcoords="offset points", xytext=(0,3), ha='center', fontsize=4, color=color1)
label = '%.2f'%overall_accuracy['2offset']
ax2.annotate(label, (2, overall_accuracy['2offset']), textcoords="offset points", xytext=(0,-6), ha='center', fontsize=4, color=color2)
label = '%.2f'%llc_coverage['2offset']
ax3.annotate(label, (2, llc_coverage['2offset']), textcoords="offset points", xytext=(0,-6), ha='center', fontsize=4, color=color3)


label = '%.2f'%speedup['3offset']
ax1.annotate(label, (3, speedup['3offset']), textcoords="offset points", xytext=(0,3), ha='center', fontsize=4, color=color1)
label = '%.2f'%overall_accuracy['3offset']
ax2.annotate(label, (3, overall_accuracy['3offset']), textcoords="offset points", xytext=(0,3), ha='center', fontsize=4, color=color2)
label = '%.2f'%llc_coverage['3offset']
ax3.annotate(label, (3, llc_coverage['3offset']), textcoords="offset points", xytext=(0,-6), ha='center', fontsize=4, color=color3)


# Show the plot
plt.tight_layout()
# plt.show()
plt.savefig('fig/fig4.pdf', dpi=1024, bbox_inches='tight', pad_inches=0.025)
