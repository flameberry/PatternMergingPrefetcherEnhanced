import os
import json
from run_functions import *


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + "/../../ChampSim")

    print(
        "Running single-core general simulations. The results can be used to generate fig. 1, 6, 7, 8, 11"
    )

    prefix = "aditya_20M_w5M"
    # num_warmup, num_simulation = 200000000, 200000000
    num_warmup, num_simulation = 5000000, 20000000
    begin, num = 0, len(workloads_all)

    for prefetcher in ["no", "pmp"]:
        run_1core(prefetcher, prefix, num_warmup, num_simulation, begin, num)

    print("Running.")


if __name__ == "__main__":
    main()
