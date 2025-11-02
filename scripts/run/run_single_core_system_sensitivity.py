import os
import json
from run_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Running sensitivity to system configurations. The results can be used to generate fig. 16')
    
    num_warmup, num_simulation = 200000000, 200000000
    begin, num = 0, 201
    
    for prefetcher in ['no', 'spp_ppf', 'vberti', 'bingo', 'dspatch', 'pmp', 'gaze']:
        for prefix, bw in [('v11', 800), ('v12', 1600), ('v13', 6400), ('v14', 12800)]: # v21 - v24
            run_1core_system_sensitivity(prefetcher, bw, 2, 0.5, prefix, num_warmup, num_simulation, begin, num)
        for prefix, llc_size in [('v24', 0.5), ('v21', 1), ('v22', 4), ('v23', 8)]: # v31 - v34
            run_1core_system_sensitivity(prefetcher, 3200, llc_size, 0.5, prefix, num_warmup, num_simulation, begin, num)
        for prefix, l2c_size in [('v25', 0.125), ('v26', 0.25), ('v27', 1), ('v28', 1.5)]: # v41 - v44
            run_1core_system_sensitivity(prefetcher, 3200, 2, l2c_size, prefix, num_warmup, num_simulation, begin, num)
    
    print('Running.')


if __name__ == '__main__':
    main()
