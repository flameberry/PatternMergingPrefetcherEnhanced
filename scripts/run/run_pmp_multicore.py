import os
import json
from run_functions import *


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + "/../../ChampSim")

    print(
        "Running multi-core homogeneous simulations. The results can be used to generate fig. 14a"
    )
    num_warmup, num_simulation = 5_000_000, 5_000_000
    begin, num = 0, len(workloads_all)
    prefix = f"aditya_warmup{num_warmup}_sim{num_simulation}"

    for core in [2, 4, 8]:
        for prefetcher in ["no", "pmp"]:
            run_multicore_homo(
                core, prefetcher, prefix, num_warmup, num_simulation, begin, num
            )

    print("Running.")


if __name__ == "__main__":
    main()
