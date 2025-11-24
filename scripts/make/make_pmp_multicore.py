# (Aditya): This file only builds 2 versions of champsim,
# ...one with no prefetcher and the other with the pmp prefetcher
import os
from make_functions import *


def main():

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + "/../../ChampSim")

    for core in [2, 4]:
        for prefetcher in ["pmp"]:
        #for prefetcher in ["no", "pmp"]:
            make_multicore(core,prefetcher)

    print("Done.")


if __name__ == "__main__":
    main()
