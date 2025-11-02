import os
import json
from run_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Running single-core general simulations. The results can be used to generate fig. 1, 6, 7, 8, 11')
    
    prefix = 'v00'
    num_warmup, num_simulation = 200000000, 200000000
    begin, num = 0, 201
    
    for prefetcher in ['no', 'ip_stride', 'spp_ppf', 'ipcp_l1', 'vberti', 'sms', 'bingo', 'dspatch', 'pmp', 'gaze', 'pc', '1offset']:
        run_1core(prefetcher, prefix, num_warmup, num_simulation, begin, num)
    
    print('Running.')


if __name__ == '__main__':
    main()
