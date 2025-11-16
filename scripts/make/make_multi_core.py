import os
import json
from make_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Making prefetchers used to generate the results of fig. 14, 15')
    
    for core in [2, 4, 8]:
        ## /// Commented Manish Kumar
        #for prefetcher in ['no', 'spp_ppf', 'vberti', 'bingo', 'dspatch', 'pmp', 'pmp_prefetch', 'gaze']:
        #    make_multicore(core, prefetcher)
        ## /// Commented Manish Kumar ends here
        ## /// Added Manish Kumar
        for prefetcher in ['pmp','pmp_enhanced']:
            make_multicore(core, prefetcher)
        ## /// Added Manish Kumar ends here
    
    print('Done.')


if __name__ == '__main__':
    main()
