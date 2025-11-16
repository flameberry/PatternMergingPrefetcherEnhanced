import os
import json
from make_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Making prefetchers used to generate the results of fig. 1, 6, 7, 8, 11, 12')
    
    ## /// Commented Manish Kumar
    # for prefetcher in ['no', 'ip_stride', 'spp_ppf', 'ipcp_l1', 'vberti', 'sms', 'bingo', 'dspatch', 'pmp', 'pmp_prefetch', 'gaze', 'pc', '1offset']:
    #     make_1core(prefetcher)
    ## /// Commented Manish Kumar ends here
    ## /// Added Manish Kumar
    for prefetcher in ['pmp','pmp_enhanced']:
        make_1core(prefetcher)
    ## /// Added Manish Kumar ends here

    print('Done.')


if __name__ == '__main__':
    main()
