import os
import json
from run_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Running single-core multi-level simulations. The results can be used to generate fig. 13')
    
    num_warmup, num_simulation = 200000000, 200000000
    begin, num = 0, 201
    
    for prefetcher_l1 in ['vberti', 'pmp', 'dspatch', 'ipcp_l1', 'gaze']:
        for prefetcher_l2 in ['spp_ppf', 'bingo']:
            prefix = 'v31' if prefetcher_l2 == 'spp_ppf' else 'v32' # spp_ppf is v11, bingo is v12
            run_1core_multi_level([prefetcher_l1, prefetcher_l2], prefix, num_warmup, num_simulation, begin, num)
            
    for prefetcher_l1 in ['ip_stride']:
        for prefix, prefetcher_l2 in [('v33', 'berti'), ('v34', 'bingo'), ('v35', 'pmp'), ('v36', 'sms'), ('v37', 'dspatch'), ('v38', 'gaze')]:
            run_1core_multi_level([prefetcher_l1, prefetcher_l2], prefix, num_warmup, num_simulation, begin, num)
    
    print('Running.')


if __name__ == '__main__':
    main()
