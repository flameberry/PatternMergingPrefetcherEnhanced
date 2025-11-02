import os
import json
from make_functions import *
    
def main():
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + '/../../ChampSim')
    
    print('Making prefetchers used to generate the results of fig. 17, 18')
    
    for prefetcher in ['gaze_sensitivity_pht128', 'gaze_sensitivity_pht256', 'gaze_sensitivity_pht512', 'gaze_sensitivity_pht1024']:
        make_1core(prefetcher)
    for prefetcher in ['gaze_sensitivity_rs512B', 'gaze_sensitivity_rs1KB', 'gaze_sensitivity_rs2KB']:
        make_1core(prefetcher)
    for prefetcher in ['vgaze', 'vgaze_sensitivity_rs8KB', 'vgaze_sensitivity_rs16KB', 'vgaze_sensitivity_rs32KB', 'vgaze_sensitivity_rs64KB']:
        make_1core(prefetcher)
    
    print('Done.')


if __name__ == '__main__':
    main()
