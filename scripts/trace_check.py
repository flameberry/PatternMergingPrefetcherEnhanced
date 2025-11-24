import os
from workloads import *

trace_dir = '../traces'

all_exist, main_exist = True, True

for workloads, benchmark_name in [(workloads_spec06, 'SPEC06'), (workloads_spec17, 'SPEC17'), (workloads_ligra, 'Ligra'), (workloads_parsec, 'PARSEC'), (workloads_cloudsuite, 'CloudSuite'), (workloads_gap, 'GAP'), (workloads_qmm, 'QMM')]:
    for workload in workloads:
        trace = f'{trace_dir}/{workload[0]}'
        if not os.path.exists(trace):
            if benchmark_name != 'GAP' and benchmark_name != 'QMM':
                main_exist = False
            all_exist = False
            print(f'{benchmark_name} {trace} does not exist!')
            
if main_exist:
    print('Main traces are prepared')
    
if all_exist:
    print('All traces are prepared')