import os
import json
from make_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Making prefetchers used to generate the results of fig. 14, 15')
    
    for core in [2, 4, 8]:
        for prefetcher in ['no', 'spp_ppf', 'vberti', 'bingo', 'dspatch', 'pmp', 'gaze']:
            make_multicore(core, prefetcher)
    
    print('Done.')


if __name__ == '__main__':
    main()
