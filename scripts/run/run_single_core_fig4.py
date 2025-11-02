import os
import json
from run_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Running single-core fig. 4 simulations. The results can be used to generate fig. 4')
    
    prefix = 'v00'
    num_warmup, num_simulation = 200000000, 200000000
    begin, num = 0, 201
    
    for prefetcher in ['2offset', '3offset', '4offset']:
        run_1core(prefetcher, prefix, num_warmup, num_simulation, begin, num)
    
    print('Running.')


if __name__ == '__main__':
    main()
