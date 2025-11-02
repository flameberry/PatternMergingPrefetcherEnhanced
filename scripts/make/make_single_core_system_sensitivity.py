import os
import json
from make_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Making prefetchers used to generate the results of fig. 16')
    
    for prefetcher in ['no', 'spp_ppf', 'vberti', 'bingo', 'dspatch', 'pmp', 'gaze']:
        make_1core_system_sensitivity(prefetcher)
    
    print('Done.')


if __name__ == '__main__':
    main()
