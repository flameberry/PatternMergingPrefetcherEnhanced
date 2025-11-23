import json
import os
import re
import sys
import numpy as np
from scipy.stats import gmean
import pandas as pd

sys.path.append('..')
from workloads import *

# speedup[num_cores][prefetcher][prefix]


def load_file_as_str(file_path):
    # print(file_path)
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        ret = f.read()
    return ret


def str2json(string):
    begin = string.find('[')
    end = string.rfind(']')+1
    return json.loads(string[begin:end])


def valid_log(str):
    if str.find('ChampSim completed all CPUs') == -1:
        return False
    else:
        return True
    

def get_raw_results(num_cores, prefetchers, prefixes, workloads, mix_type = 'homo'):
    
    if mix_type not in ['hete', 'homo', 'both']:
        print('Mix type can be [\'hete\', \'homo\', \'both\']. The default value is \'homo\'.')
        exit(0)
        
    workloads_hete = None
    if num_cores == 2:
        workloads_hete = workloads_all_2core_heterogeneous
    elif num_cores == 4:
        workloads_hete = workloads_all_4core_heterogeneous
    elif num_cores == 8:
        workloads_hete = workloads_all_8core_heterogeneous
        
    workloads_simplified = []
    json_root_path = '../../json/'+str(num_cores)+'core/'
    log_root_path = '../../log/'+str(num_cores)+'core/'

    ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless, l1d_load_miss, l2c_load_miss = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

    json_file_lists = {}
    for prefetcher in prefetchers:
        json_file_lists[prefetcher] = []
        
        if num_cores == 1: # single_core
            for workload in workloads:
                json_file_lists[prefetcher].append(workload[1])
            for i in range(len(json_file_lists[prefetcher])):
                json_file_lists[prefetcher][i] = f'{prefixes[prefetcher]}-{json_file_lists[prefetcher][i]}.json'
        else: # multi_core
            json_file_list_homo, json_file_list_hete = [], []
            for workload in workloads:
                json_file_list_homo.append(workload[1])
            for i in range(len(json_file_list_homo)):
                json_file_list_homo[i] = f'{prefixes[prefetcher]}-{json_file_list_homo[i]}.json'
            
            if mix_type in ['hete', 'both']:
                trace_list_hete = None
                # if num_cores == 2:
                trace_list_hete = workloads_hete
                for trace in trace_list_hete:
                    file_name = f'{prefixes[prefetcher]}-'
                    for i in range(num_cores):
                        file_name += trace[i][1]
                        if (i != num_cores-1):
                            file_name += '-'
                    file_name += '.json'
                    json_file_list_hete.append(file_name)
                    
            if mix_type == 'both':
                json_file_lists[prefetcher] = json_file_list_homo + json_file_list_hete
            elif mix_type == 'homo':
                json_file_lists[prefetcher] = json_file_list_homo
            elif mix_type == 'hete':
                json_file_lists[prefetcher] = json_file_list_hete
            # print(file_lists)
            
    for file in json_file_lists['no']: 
        workload = file[len(prefixes['no'])+1:-5] # v00-{simplified_workload_name}.json
        workloads_simplified.append(workload)
    
    for d in [ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless, l1d_load_miss, l2c_load_miss]:
        for prefetcher in prefetchers:
            d[prefetcher] = {}
            for workload in workloads_simplified:
                d[prefetcher][workload] = [None for i in range(num_cores)]
    
    for prefetcher in prefetchers:
        # print(prefetcher)
        for file in json_file_lists[prefetcher]:
            workload = file[len(prefixes[prefetcher])+1:-5]
            # print(file)
            json_file = f'{json_root_path}{prefetcher}/{file}'
            log_file = f'{log_root_path}{prefetcher}/{file[0:-4]}log'
            log_str = load_file_as_str(log_file)
            
            if(valid_log(log_str)):
                try:
                    json_str = load_file_as_str(json_file)
                    # print(json_file)
                    json_obj = str2json(json_str)
                    
                    # Add a check for an empty list
                    if not json_obj:
                         raise IndexError("JSON list is empty")

                    for i in range(num_cores):
                        ipc[prefetcher][workload][i] = json_obj[0]['roi']['cores'][i]['instructions']/json_obj[0]['roi']['cores'][i]['cycles']
                        cycles[prefetcher][workload][i] = json_obj[0]['roi']['cores'][i]['cycles']
                        l1_pf_useful[prefetcher][workload][i] = json_obj[0]['roi']['cpu'+str(i)+'_L1D']["prefetch useful"]
                        l1_pf_useless[prefetcher][workload][i] = json_obj[0]['roi']['cpu'+str(i)+'_L1D']["prefetch useless"]
                        l1_pf_late[prefetcher][workload][i] = json_obj[0]['roi']['cpu'+str(i)+'_L1D']['prefetch late']
                        llc_load_miss[prefetcher][workload][i] = json_obj[0]['roi']['LLC']['LOAD']['miss'][i]
                        l2_pf_useful[prefetcher][workload][i] = json_obj[0]['roi']['cpu'+str(i)+'_L2C']['pf_useful_at_l2_from_l1']
                        l2_pf_useless[prefetcher][workload][i] = json_obj[0]['roi']['cpu'+str(i)+'_L2C']['pf_useless_at_l2_from_l1']
                        l1d_load_miss[prefetcher][workload][i] = json_obj[0]['roi']['cpu'+str(i)+'_L1D']['LOAD']['miss']
                        l2c_load_miss[prefetcher][workload][i] = json_obj[0]['roi']['cpu'+str(i)+'_L2C']['LOAD']['miss']
                
                # Catch the specific JSON error
                except json.decoder.JSONDecodeError:
                    print(f"JSON ERROR: {prefetcher}, file {file} is corrupt or empty.")
                # Catch if json_obj is [] and json_obj[0] fails
                except IndexError:
                    print(f"JSON ERROR: {prefetcher}, file {file} is valid JSON but has an empty list [].")
                # Catch any other unexpected parsing errors
                except Exception as e:
                     print(f"UNEXPECTED ERROR parsing {file}: {e}")
            else:
                # I also recommend making this message clearer
                print(prefetcher, 'Invalid LOG', file)
                            
    return ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless, workloads_simplified, l1d_load_miss, l2c_load_miss


def calculate_l2_accuracy(l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless, prefetchers, workloads, num_cores):
    l2_accuracy, l2_ratio, overall_accuracy = {}, {}, {}
    for prefetcher in prefetchers:
        if prefetcher != 'no':
            accuracy_tmp, l2_ratio_tmp, overall_accuracy_tmp = [], [], []
            for workload in workloads:
                for i in range(num_cores):
                    accuracy_tmp.append(l2_pf_useful[prefetcher][workload[1]][i]/(l2_pf_useful[prefetcher][workload[1]][i]+l2_pf_useless[prefetcher][workload[1]][i]) if l2_pf_useful[prefetcher][workload[1]][i] != 0 else 0)
                    l2_ratio_tmp.append(((l2_pf_useful[prefetcher][workload[1]][i]+l2_pf_useless[prefetcher][workload[1]][i]) / (l2_pf_useful[prefetcher][workload[1]][i]+l2_pf_useless[prefetcher][workload[1]][i]+l1_pf_useful[prefetcher][workload[1]][i] + l1_pf_useless[prefetcher][workload[1]][i]))) if l1_pf_useful[prefetcher][workload[1]][i] != 0 else 0
                    overall_accuracy_tmp.append(((l2_pf_useful[prefetcher][workload[1]][i]+l1_pf_useful[prefetcher][workload[1]][i]) / (l2_pf_useful[prefetcher][workload[1]][i]+l2_pf_useless[prefetcher][workload[1]][i]+l1_pf_useful[prefetcher][workload[1]][i] + l1_pf_useless[prefetcher][workload[1]][i]))) if l1_pf_useful[prefetcher][workload[1]][i] != 0 else 0
                    
            l2_accuracy[prefetcher] = np.mean(accuracy_tmp)
            l2_ratio[prefetcher] = np.mean(l2_ratio_tmp)
            overall_accuracy[prefetcher] = np.mean(overall_accuracy_tmp)

    return l2_accuracy, l2_ratio, overall_accuracy


def calculate_late_ratio(l1_pf_late, l1_pf_useful, prefetchers, workloads, num_cores):
    late = {}
    for prefetcher in prefetchers:
        if prefetcher != 'no':
            late_tmp = []
            for workload in workloads:
                for i in range(num_cores):
                    late_tmp.append(1 if l1_pf_useful[prefetcher][workload][i] == 0 else (0.01 if l1_pf_late[prefetcher][workload][i] == 0 else l1_pf_late[prefetcher][workload][i] / l1_pf_useful[prefetcher][workload][i]))
            late[prefetcher] = np.mean(late_tmp)

    return late


def eliminate_invalid_values(d, prefetchers, workloads):
    for prefetcher in prefetchers:
        for workload in workloads:
            for core in range(len(d[prefetcher][workload])):
                if d[prefetcher][workload][core] == None:
                    sum, num = 0, 0
                    for pref in prefetchers:
                        if pref != 'no' and d[pref][workload][core] != None:
                            sum+=d[pref][workload][core]
                            num+=1
                    d[prefetcher][workload][core] = sum/num
    pass


def get_singlecore_speedup(prefetchers, prefixes, workloads):
    ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless, workloads_simplified = get_raw_results(1, prefetchers, prefixes, workloads)
    
    for d in [ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless]:
        eliminate_invalid_values(d, prefetchers, workloads_simplified)
        
    speedup = {}
    for prefetcher in prefetchers:
        tmp = []
        for workload in workloads_simplified:
            tmp.append(cycles['no'][workload][0]/cycles[prefetcher][workload][0])
        tmp.sort()
        speedup[prefetcher] = gmean(tmp)
        
    return speedup


def get_singlecore_speedup_detail(prefetchers, prefixes, workloads):
    ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless, workloads_simplified = get_raw_results(1, prefetchers, prefixes, workloads)
    
    for d in [ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless]:
        eliminate_invalid_values(d, prefetchers, workloads_simplified)
        
    speedup_detail = {}
    for prefetcher in prefetchers:
        speedup_detail[prefetcher] = {}
        for workload in workloads_simplified:
            speedup_detail[prefetcher][workload] = cycles['no'][workload][0]/cycles[prefetcher][workload][0]
    return speedup_detail


def get_singecore_coverage_accuracy(prefetchers, prefixes, workloads):
    ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless, workloads_simplified = get_raw_results(1, prefetchers, prefixes, workloads)
    
    for d in [ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless]:
        eliminate_invalid_values(d, prefetchers, workloads_simplified)
        
    llc_coverage, overall_accuracy = {}, {}
    for prefetcher in prefetchers:
        if prefetcher != 'no':
            llc_coverage_tmp, overall_accuracy_tmp = [], []
            for workload in workloads_simplified:
                
                # --- FIX START ---
                # Check for divide-by-zero when baseline misses are 0
                baseline_misses = llc_load_miss['no'][workload][0]
                prefetcher_misses = llc_load_miss[prefetcher][workload][0]
                
                if baseline_misses > 0:
                    # Normal case
                    coverage_val = 1 - (prefetcher_misses / baseline_misses)
                    llc_coverage_tmp.append(coverage_val if coverage_val < 1 else 0) # Keep original logic
                else:
                    # Baseline had 0 misses
                    if prefetcher_misses == 0:
                        llc_coverage_tmp.append(1.0) # Perfect coverage
                    else:
                        llc_coverage_tmp.append(0.0) # Prefetcher added misses
                # --- FIX END ---


                # --- FIX START ---
                # Check for divide-by-zero when total prefetches are 0
                l2_useful = l2_pf_useful[prefetcher][workload][0]
                l2_useless = l2_pf_useless[prefetcher][workload][0]
                l1_useful = l1_pf_useful[prefetcher][workload][0]
                l1_useless = l1_pf_useless[prefetcher][workload][0]
                
                total_useful = l2_useful + l1_useful
                total_prefetches = total_useful + l2_useless + l1_useless

                if total_prefetches > 0:
                    overall_accuracy_tmp.append(total_useful / total_prefetches)
                else:
                    # No prefetches were issued, so accuracy is 0 (or undefined, 0 is safer)
                    overall_accuracy_tmp.append(0.0) 
                # --- FIX END ---
                
            llc_coverage[prefetcher] = np.mean(llc_coverage_tmp)
            overall_accuracy[prefetcher] = np.mean(overall_accuracy_tmp)

    return llc_coverage, overall_accuracy

def get_late_ratio(prefetchers, prefixes, workloads):
    ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless, workloads_simplified = get_raw_results(1, prefetchers, prefixes, workloads)
    
    for d in [ipc, cycles, llc_load_miss, l1_pf_late, l1_pf_useful, l1_pf_useless, l2_pf_useful, l2_pf_useless]:
        eliminate_invalid_values(d, prefetchers, workloads_simplified)
        
    late = calculate_late_ratio(l1_pf_late, l1_pf_useful, prefetchers, workloads_simplified, 1)
    return late


def get_multicore_speedup(num_cores, prefetchers, prefixes, workloads, mix_type = 'homo'):
    
    ipc, cycles, _, _, _, _, _, _, workloads_simplified = get_raw_results(num_cores, prefetchers, prefixes, workloads, mix_type)
    
    for d in [ipc, cycles]:
        eliminate_invalid_values(d, prefetchers, workloads_simplified)
        
    speedup = {}
    for prefetcher in prefetchers:
        tmp = []
        for workload in workloads_simplified:
            for i in range(num_cores):
                tmp.append(cycles['no'][workload][i]/cycles[prefetcher][workload][i])
        tmp.sort()
        speedup[prefetcher] = gmean(tmp)
        
    return speedup


def get_multicore_speedup_detail(num_cores, prefetchers, prefixes, workloads, mix_type = 'homo'):
    ipc, cycles, _, _, _, _, _, _, workloads_simplified = get_raw_results(num_cores, prefetchers, prefixes, workloads, mix_type)
    
    for d in [ipc, cycles]:
        eliminate_invalid_values(d, prefetchers, workloads_simplified)
        
    speedup_detail = {}
    for prefetcher in prefetchers:
        speedup_detail[prefetcher] = {}
        for workload in workloads_simplified:
            speedup_detail[prefetcher][workload] = []
            # print(workload)
            for i in range(num_cores):
                speedup_detail[prefetcher][workload].append(cycles['no'][workload][i]/cycles[prefetcher][workload][i])
    return speedup_detail
