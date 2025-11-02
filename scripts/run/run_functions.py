import os
import json
import sys
sys.path.append('..')
from workloads import *


def run_1core(prefetcher, prefix, num_warmup, num_simulation, begin, num):
    name = f'champsim_1core_{prefetcher}'
    
    dir_check = ['../log/1core', f'../log/1core/{prefetcher}', '../json/1core', f'../json/1core/{prefetcher}']
    for dir in dir_check:
        if not os.path.exists(dir):
            os.makedirs(dir)
    
    for workload in workloads_all[begin:begin+num]:
        trace = f' ../traces/{workload[0]}'
        run_command = f'nohup ./bin/{name} --json=../json/1core/{prefetcher}/{prefix}-{workload[1]}.json'
        if workload[2] == True:
            run_command += ' -c' 
        run_command += f" --warmup_instructions {num_warmup} --simulation_instructions {num_simulation}"
        run_command += trace
        run_command += f'> ../log/1core/{prefetcher}/{prefix}-{workload[1]}.log'
        run_command += " 2>& 1&"
        os.system(run_command)
        
        
def run_1core_gap(prefetcher, prefix, num_warmup, num_simulation, begin, num):
    name = f'champsim_1core_{prefetcher}'
    
    dir_check = ['../log/1core', f'../log/1core/{prefetcher}', '../json/1core', f'../json/1core/{prefetcher}']
    for dir in dir_check:
        if not os.path.exists(dir):
            os.makedirs(dir)
            
    for workload in workloads_gap[begin:begin+num]:
        trace = f' ../traces/{workload[0]}'
        run_command = f'nohup ./bin/{name} --json=../json/1core/{prefetcher}/{prefix}-{workload[1]}.json'
        if workload[2] == True:
            run_command += ' -c' 
        run_command += f" --warmup_instructions {num_warmup} --simulation_instructions {num_simulation}"
        run_command += trace
        run_command += f'> ../log/1core/{prefetcher}/{prefix}-{workload[1]}.log'
        run_command += " 2>& 1&"
        os.system(run_command)
        
        
def run_1core_qmm(prefetcher, prefix, num_warmup, num_simulation, begin, num):
    name = f'champsim_1core_{prefetcher}'
    
    dir_check = ['../log/1core', f'../log/1core/{prefetcher}', '../json/1core', f'../json/1core/{prefetcher}']
    for dir in dir_check:
        if not os.path.exists(dir):
            os.makedirs(dir)
            
    for workload in workloads_qmm[begin:begin+num]:
        trace = f' ../traces/{workload[0]}'
        run_command = f'nohup ./bin/{name} --json=../json/1core/{prefetcher}/{prefix}-{workload[1]}.json'
        if workload[2] == True:
            run_command += ' -c' 
        run_command += f" --warmup_instructions {num_warmup} --simulation_instructions {num_simulation}"
        run_command += trace
        run_command += f'> ../log/1core/{prefetcher}/{prefix}-{workload[1]}.log'
        run_command += " 2>& 1&"
        os.system(run_command)
        

def run_1core_multi_level(prefetchers, prefix, num_warmup, num_simulation, begin, num):
    name = 'champsim_1core_' + prefetchers[0] + '_' + prefetchers[1]
    
    
    dir_check = ['../log/1core', f'../log/1core/{prefetchers[0]}', '../json/1core', f'../json/1core/{prefetchers[0]}']
    for dir in dir_check:
        if not os.path.exists(dir):
            os.makedirs(dir)
    
    for workload in workloads_all[begin:begin+num]:
        trace = f' ../traces/{workload[0]}'
        run_command = f'nohup ./bin/{name} --json=../json/1core/{prefetchers[0]}/{prefix}-{workload[1]}.json'
        if workload[2] == True:
            run_command += ' -c' 
        run_command += f" --warmup_instructions {num_warmup} --simulation_instructions {num_simulation}"
        run_command += trace
        run_command += f'> ../log/1core/{prefetchers[0]}/{prefix}-{workload[1]}.log'
        run_command += " 2>& 1&"
        os.system(run_command)
        

def run_1core_system_sensitivity(prefetcher, bw, llc_size, l2c_size, prefix, num_warmup, num_simulation, begin, num):
    name = f'champsim_1core_{prefetcher}_bw_{bw}_l2c_{l2c_size}_llc_{llc_size}'
    
    dir_check = ['../log/1core', f'../log/1core/{prefetcher}', '../json/1core', f'../json/1core/{prefetcher}']
    for dir in dir_check:
        if not os.path.exists(dir):
            os.makedirs(dir)
            
    for workload in workloads_all[begin:begin+num]:
        trace = f' ../traces/{workload[0]}'
        run_command = f'nohup ./bin/{name} --json=../json/1core/{prefetcher}/{prefix}-{workload[1]}.json'
        if workload[2] == True:
            run_command += ' -c' 
        run_command += f" --warmup_instructions {num_warmup} --simulation_instructions {num_simulation}"
        run_command += trace
        run_command += f'> ../log/1core/{prefetcher}/{prefix}-{workload[1]}.log'
        run_command += " 2>& 1&"
        os.system(run_command)
        

def run_1core_gaze_sensitivity(prefetcher, prefix, num_warmup, num_simulation, begin, num):
    name = f'champsim_1core_{prefetcher}'
    
    dir_check = ['../log/1core', f'../log/1core/{prefetcher}', '../json/1core', f'../json/1core/{prefetcher}']
    for dir in dir_check:
        if not os.path.exists(dir):
            os.makedirs(dir)
    
    for workload in workloads_all[begin:begin+num]:
        trace = f' ../traces/{workload[0]}'
        run_command = f'nohup ./bin/{name} --json=../json/1core/{prefetcher}/{prefix}-{workload[1]}.json'
        if workload[2] == True:
            run_command += ' -c' 
        run_command += f" --warmup_instructions {num_warmup} --simulation_instructions {num_simulation}"
        run_command += trace
        run_command += f'> ../log/1core/{prefetcher}/{prefix}-{workload[1]}.log'
        run_command += " 2>& 1&"
        os.system(run_command)
        

def run_multicore_hete(num_cores, prefetcher, prefix, num_warmup, num_simulation, begin, num):
    name = f'champsim_{num_cores}core_{prefetcher}'
    
    dir_check = [f'../log/{num_cores}core', f'../log/{num_cores}core/{prefetcher}', f'../json/{num_cores}core', f'../json/{num_cores}core/{prefetcher}']
    for dir in dir_check:
        if not os.path.exists(dir):
            os.makedirs(dir)
    
    workloads_all_multicore = None
    if num_cores == 2:
        workloads_all_multicore = workloads_all_2core_heterogeneous
    elif num_cores == 4:
        workloads_all_multicore = workloads_all_4core_heterogeneous
    elif num_cores == 8:
        workloads_all_multicore = workloads_all_8core_heterogeneous
        
    for workload in workloads_all_multicore[begin:begin+num]:
        traces = [None for i in range(num_cores)]
        for i in range(num_cores):
            traces[i] = f' ../traces/{workload[i][0]}'
        run_command = f'nohup ./bin/{name} --warmup_instructions {num_warmup} --simulation_instructions {num_simulation}'
        if workload[0][2] == True:
            run_command += ' -c' 
        for i in range(num_cores):
            run_command += traces[i]
            run_command += ' '
        run_command += f'> ../log/{num_cores}core/{prefetcher}/{prefix}-'
        for i in range(num_cores):
            run_command += workload[i][1]
            if (i != num_cores-1):
                run_command += '-'
        run_command += '.log ' 
        run_command += f'--json=../json/{num_cores}core/{prefetcher}/{prefix}-'
        for i in range(num_cores):
            run_command += workload[i][1]
            if (i != num_cores-1):
                run_command += '-'
        run_command += '.json ' 
        run_command += '2>& 1&'
        os.system(run_command)

def run_multicore_homo(num_cores, prefetcher, prefix, num_warmup, num_simulation, begin, num):
    name = f'champsim_{num_cores}core_{prefetcher}'
    
    dir_check = [f'../log/{num_cores}core', f'../log/{num_cores}core/{prefetcher}', f'../json/{num_cores}core', f'../json/{num_cores}core/{prefetcher}']
    for dir in dir_check:
        if not os.path.exists(dir):
            os.makedirs(dir)
            
    for workload in workloads_all[begin:begin+num]:
        trace = f' ../traces/{workload[0]}'
        run_command = f'nohup ./bin/{name} --warmup_instructions {num_warmup} --simulation_instructions {num_simulation}'
        if workload[2] == True:
            run_command += ' -c' 
        for i in range(num_cores):
            run_command += trace
            run_command += ' '
        run_command += f'> ../log/{num_cores}core/{prefetcher}/{prefix}-{workload[1]}.log'
        run_command += f' --json=../json/{num_cores}core/{prefetcher}/{prefix}-{workload[1]}.json' 
        run_command += ' 2>& 1&'
        os.system(run_command)