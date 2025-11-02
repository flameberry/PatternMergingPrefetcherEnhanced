import os
import json
from run_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Running multi-core homogeneous simulations. The results can be used to generate fig. 14a')
    
    prefix = 'v00'
    num_warmup, num_simulation = 200000000, 200000000
    begin, num = 0, 201
    
    for core in [2, 4, 8]:
        for prefetcher in ['no', 'spp_ppf', 'vberti', 'bingo', 'dspatch', 'pmp', 'gaze']:
            run_multicore_homo(core, prefetcher, prefix, num_warmup, num_simulation, begin, num)
    
    print('Running.')


if __name__ == '__main__':
    main()
