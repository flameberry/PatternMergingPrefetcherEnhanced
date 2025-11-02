import os
import json
from run_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Running sensitivity to gaze configurations. The results can be used to generate fig. 17, 18')
    
    prefix = 'v00'
    num_warmup, num_simulation = 200000000, 200000000
    begin, num = 0, 201
    
    for prefetcher in ['gaze_sensitivity_pht128', 'gaze_sensitivity_pht256', 'gaze_sensitivity_pht512', 'gaze_sensitivity_pht1024']:
        run_1core(prefetcher, prefix, num_warmup, num_simulation, begin, num)
    for prefetcher in ['gaze_sensitivity_rs512B', 'gaze_sensitivity_rs1KB', 'gaze_sensitivity_rs2KB']:
        run_1core(prefetcher, prefix, num_warmup, num_simulation, begin, num)
    for prefetcher in ['vgaze', 'vgaze_sensitivity_rs8KB', 'vgaze_sensitivity_rs16KB', 'vgaze_sensitivity_rs32KB', 'vgaze_sensitivity_rs64KB']:
        run_1core(prefetcher, prefix, num_warmup, num_simulation, begin, num)
    
    print('Running.')


if __name__ == '__main__':
    main()
