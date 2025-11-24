import os
import json
from run_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Running gaze performance analysis. The results can be used to generate fig. 9, 10')
    
    prefix = 'v00'
    num_warmup, num_simulation = 200000000, 200000000
    begin, num = 0, 201
    
    for prefetcher in ['gaze_analysis_pht', '1offset', 'gaze_analysis_pht4ss', 'gaze_analysis_sm4ss']:
        run_1core(prefetcher, prefix, num_warmup, num_simulation, begin, num)
    
    print('Running.')


if __name__ == '__main__':
    main()
