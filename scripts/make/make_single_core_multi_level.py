import os
import json
from make_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Making prefetchers used to generate the results of fig. 13')
    
    for prefetcher_l1 in ['vberti', 'pmp', 'dspatch', 'ipcp_l1', 'gaze']:
        for prefetcher_l2 in ['spp_ppf', 'bingo']:
            make_1core_multi_level([prefetcher_l1, prefetcher_l2])
            
    for prefetcher_l1 in ['ip_stride']:
        for prefetcher_l2 in ['berti', 'bingo', 'pmp', 'sms', 'dspatch', 'gaze']:
            make_1core_multi_level([prefetcher_l1, prefetcher_l2])
    
    print('Done.')


if __name__ == '__main__':
    main()
