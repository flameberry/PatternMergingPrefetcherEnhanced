import os
import json
from run_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Running single-core fig. 12 simulations. The results can be used to generate fig. 12')
    
    prefix = 'v00'
    num_warmup, num_simulation = 200000000, 200000000
    begin, num = 0, 201
    
    for prefetcher in ['no', 'vberti', 'pmp', 'gaze']:
        run_1core_gap(prefetcher, prefix, num_warmup, num_simulation, begin, num)
        
    num_warmup, num_simulation = 10000000, 20000000
    for prefetcher in ['no', 'vberti', 'pmp', 'gaze']:
        run_1core_qmm(prefetcher, prefix, num_warmup, num_simulation, begin, num)
    
    print('Running.')


if __name__ == '__main__':
    main()
