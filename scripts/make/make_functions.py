
import os
import json

def modify_config_1core(branch, prefetcher, name):
    with open("./champsim_config.json", "r") as f:
        load_dict = json.load(f)

    load_dict['ooo_cpu'][0]['branch_predictor'] = branch
    load_dict['L1D']['prefetcher'] = prefetcher[1:] if (prefetcher[0] == 'v') else prefetcher
    load_dict['executable_name'] = name

    load_dict['L1D']['virtual_prefetch'] = True if (prefetcher[0] == 'v') else False

    with open("./champsim_config_auto.json", "w") as f:
        json.dump(load_dict, f)
    pass


def make_1core(prefetcher):
    name = f'champsim_1core_{prefetcher}'
    modify_config_1core('hashed_perceptron', prefetcher, name)
    os.system('./config.sh ./champsim_config_auto.json')
    os.system('make clean && make -j16')


def modify_config_1core_multi_level(branch, prefetchers, name):
    with open("./champsim_config.json", "r") as f:
        load_dict = json.load(f)

    load_dict['executable_name'] = name
    load_dict['ooo_cpu'][0]['branch_predictor'] = branch
    
    load_dict['L1D']['prefetcher'] = prefetchers[0][1:] if prefetchers[0][0] == 'v' else prefetchers[0]
    load_dict['L1D']['virtual_prefetch'] = True if prefetchers[0][0] == 'v' else False

    load_dict['L2C']['prefetcher'] = prefetchers[1]


    with open("./champsim_config_auto.json", "w") as f:
        json.dump(load_dict, f)
    pass


def make_1core_multi_level(prefetchers):
    name = f'champsim_1core_{prefetchers[0]}_{prefetchers[1]}'
    modify_config_1core_multi_level('hashed_perceptron', prefetchers, name)
    os.system('./config.sh champsim_config_auto.json')
    os.system('make clean && make -j16')
    
    
def modify_config_1core_system_sensitivity(branch, prefetcher, bw, llc_size, l2c_size, name):
    if bw not in [800, 1600, 3200, 6400, 12800] or llc_size not in [0.5, 1, 2, 4, 8] or l2c_size not in [0.125, 0.25, 0.5, 1, 1.5]:
        print('Wrong bw or llc_size:', bw, llc_size, l2c_size)
        exit()

    llc_dict = {0.5:4, 1:8, 2:16, 4:32, 8:64}
    l2c_latency_dict = {0.125:6, 0.25:7, 0.5:10, 1:12, 1.5:15}
    l2c_set_dict = {0.125:512, 0.25:512, 0.5:1024, 1:1024, 1.5:1536}
    l2c_way_dict = {0.125:4, 0.25:8, 0.5:8, 1:16, 1.5:16}

    with open("./champsim_config.json", "r") as f:
        load_dict = json.load(f)

    load_dict['ooo_cpu'][0]['branch_predictor'] = branch
    load_dict['L1D']['prefetcher'] = prefetcher[1:] if (prefetcher[0] == 'v') else prefetcher
    load_dict['executable_name'] = name
    load_dict['L1D']['virtual_prefetch'] = True if (prefetcher[0] == 'v') else False


    load_dict['L2C']['sets'] = l2c_set_dict[l2c_size]
    load_dict['L2C']['ways'] = l2c_way_dict[l2c_size]
    load_dict['L2C']['latency'] = l2c_latency_dict[l2c_size]

    load_dict['LLC']['ways'] = llc_dict[llc_size]
    load_dict['physical_memory']['frequency'] = bw
 
    with open("./champsim_config_auto.json", "w") as f:
        json.dump(load_dict, f)
    pass
    
    
def make_1core_system_sensitivity(prefetcher):

    # varying Bandwidth
    bw, llc_size, l2c_size = 3200, 2, 0.5
    for bw in [800, 1600, 6400, 12800]:
        name = f'champsim_1core_{prefetcher}_bw_{bw}_l2c_{l2c_size}_llc_{llc_size}'
        modify_config_1core_system_sensitivity('hashed_perceptron', prefetcher, bw, llc_size, l2c_size, name)
        os.system('./config.sh champsim_config_auto.json')
        os.system('make clean && make -j16')

    # varying LLC Size
    bw, llc_size, l2c_size = 3200, 2, 0.5
    for llc_size in [0.5, 1, 4, 8]:
        name = f'champsim_1core_{prefetcher}_bw_{bw}_l2c_{l2c_size}_llc_{llc_size}'
        modify_config_1core_system_sensitivity('hashed_perceptron', prefetcher, bw, llc_size, l2c_size, name)
        os.system('./config.sh champsim_config_auto.json')
        os.system('make clean && make -j16')
        
    # varying L2C Size
    bw, llc_size, l2c_size = 3200, 2, 0.5
    for l2c_size in [0.125, 0.25, 1, 1.5]:
        name = f'champsim_1core_{prefetcher}_bw_{bw}_l2c_{l2c_size}_llc_{llc_size}'
        modify_config_1core_system_sensitivity('hashed_perceptron', prefetcher, bw, llc_size, l2c_size, name)
        os.system('./config.sh champsim_config_auto.json')
        os.system('make clean && make -j16')
        
def modify_config_multicore(num_cores, branch, prefetcher, name):
    if (num_cores not in [2, 4, 8, 16]):
        print('Wrong num_cores!')
        exit()
    with open("./champsim_config.json", "r") as f:
        load_dict = json.load(f)

    load_dict['ooo_cpu'][0]['branch_predictor'] = branch
    load_dict['L1D']['prefetcher'] = prefetcher[1:] if (prefetcher[0] == 'v') else prefetcher
    load_dict['num_cores'] = num_cores
    load_dict['executable_name'] = name

    load_dict['L1D']['virtual_prefetch'] = True if prefetcher[0] == 'v' else False

    # LLC: 2 M/core, 16 ways
    load_dict['LLC']['wq_size'] = num_cores*load_dict['LLC']['wq_size']
    load_dict['LLC']['pq_size'] = num_cores*load_dict['LLC']['pq_size']
    load_dict['LLC']['rq_size'] = num_cores*load_dict['LLC']['rq_size']
    load_dict['LLC']['mshr_size'] = num_cores*load_dict['LLC']['mshr_size']
    load_dict['LLC']['sets'] = num_cores*load_dict['LLC']['sets']

    # num_cores
    for i in range(1, num_cores):
        load_dict['ooo_cpu'].append(load_dict['ooo_cpu'][0])
    # DRAM: 1 ranks/channel, 2 banks/rank, 2 channels, 2 KB row buffer/bank
    # default: 1core -> 4 GB, 4core -> 2 channels
    # default: 1 1 8 65536 128
    # DRAM_CHANNELS * DRAM_RANKS * DRAM_BANKS * DRAM_ROWS * DRAM_COLUMNS * BLOCK_SIZE
    if num_cores == 2:
        load_dict['physical_memory']['channels'] = 2
    elif num_cores == 4:
        load_dict['physical_memory']['channels'] = 2
        load_dict['physical_memory']['ranks'] = 2
    elif num_cores == 8:
        load_dict['physical_memory']['channels'] = 4
        load_dict['physical_memory']['ranks'] = 2
    # rq_size, wq_size are per channel parameterss

    with open("./champsim_config_auto.json", "w") as f:
        json.dump(load_dict, f)
    pass


def make_multicore(num_cores, prefetcher):
    name = 'champsim_' + str(num_cores) + 'core_' + prefetcher
    modify_config_multicore(num_cores, 'hashed_perceptron', prefetcher, name)
    os.system('./config.sh champsim_config_auto.json')
    os.system('make clean && make -j16')
