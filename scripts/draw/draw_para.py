import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['hatch.linewidth'] = 0.5

benchmark_dict = {'spec06': 'SPEC06', 'spec17': 'SPEC17', 'spec06_spec17': 'SPEC', 'ligra': 'Ligra', 'parsec': 'PARSEC', 'cloudsuite': 'Cloud', 'all': 'AVG'}
prefetcher_dict = {'spp_ppf': 'SPP-PPF', 'ipcp_l1': 'IPCP-L1', 'berti': 'Berti', 'vberti': 'vBerti', 'sms': 'SMS', 'bingo': 'Bingo', 'dspatch': 'DSPatch', 'pmp': 'PMP', 'gaze': 'Gaze', 'ip_stride': 'IP-stride'}

color_dict = {'ip_stride': '#777777', 'spp_ppf': '#CCCCCC', 'ipcp_l1': '#4C4C4C', 'berti': 'white', 'vberti': 'white', 'sms': 'black', 'bingo': '#4C4C4C', 'dspatch': 'white', 'pmp': '#CCCCCC', 'gaze': 'black', 'late':'#EEEEEE'}
hatch_dict = {'ip_stride': None, 'spp_ppf': None, 'ipcp_l1': '----', 'berti': '----', 'vberti': '----', 'sms': '\\\\\\\\', 'bingo': None, 'dspatch': '////', 'pmp': '....', 'gaze': None}
edgecolor_dict = {'ip_stride': 'black', 'spp_ppf': 'black', 'ipcp_l1': 'white', 'berti': 'black', 'vberti': 'black', 'sms': 'white', 'bingo': 'black', 'dspatch': 'black', 'pmp': 'black', 'gaze': 'white'}

marker_dict = {'ip_stride': '>', 'spp_ppf': '>', 'ipcp_l1': '*', 'berti': '^', 'vberti': '^', 'sms': 'o', 'bingo': 's', 'dspatch': 'v', 'pmp': 'd', 'gaze': '<'}
linecolor_dict = {'ip_stride': '#2A72B3', 'spp_ppf': '#2A72B3', 'ipcp_l1': '#A8B3C3', 'berti': '#4BACC6', 'vberti': '#4BACC6', 'sms': '#729ECD', 'bingo': '#5c5c5c', 'dspatch': '#7976a2', 'pmp': '#63bbb0', 'gaze': 'black'}

