import argparse
from os.path import join

from lightning_network.settings import available_topologies, TOPOLOGY_DIR
from lightning_network.simulation import simulate


def main():
    parser = argparse.ArgumentParser(description="Lightning network simulator")
    parser.add_argument("-b","--boundaries", nargs=2, metavar=("MIN", "MAX"), type=int, default=[20, 100],
                        help="the minimum and minimum amount of money to transfer (20 and 100 by default)")
    parser.add_argument("-n","--number_tx", type=int, default=1,
                        help="number of transactions to simulate")
    parser.add_argument("-t", type=str, choices=available_topologies(), default="topology1.json",
                        help="Topology of the lightning network")
    parser.add_argument("-o","--output", type=str, default=None,
                        help="The output file for the simulation")
    args = parser.parse_args()

    topology_file_path = join(TOPOLOGY_DIR, args.t)
    simulate(topology_file_path, args.number_tx, args.boundaries[0], args.boundaries[1], args.output)
