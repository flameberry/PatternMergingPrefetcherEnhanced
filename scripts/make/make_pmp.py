# (Aditya): This file only builds 2 versions of champsim,
# ...one with no prefetcher and the other with the pmp prefetcher
import os
from make_functions import *


def main():

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir + "/../../ChampSim")

    for prefetcher in ["no", "pmp"]:
        make_1core(prefetcher)

    print("Done.")


if __name__ == "__main__":
    main()
