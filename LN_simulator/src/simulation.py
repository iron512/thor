from random import choice, randint

import networkx as nx

from src.algorithms import ref, compute_cheapest_paths, heuristic_paths
from src.listener import Listener
from src.messages import Tx, NotifyNoPath
from src.network import generate_network


def simulate(topology_file_path: str, n_txs: int, min_amount: int, max_amount: int, output: str):
    """
    Starts the simulation.
    The simulation performs the specified number of transaction.
    Each transaction attempts to transfer a random amount of money within the specified bounds, and can have a positive
    or negative outcome.
    :param n_txs: number of transactions to simulate
    :param min_amount: minimum amount of money to transfer (20 by default)
    :param max_amount: maximum amount of money to transfer (100 by default)
    """

    ln: nx.DiGraph = generate_network(topology_file_path)

    if nx.is_strongly_connected(ln):
        print("Network is strongly connected")
    else:
        print(f"WARNING: network is not strongly connected")
    print(f"{len(ln.nodes)} nodes: {ln.nodes}")
    print("Channels:")
    for data in ln.edges.data():
        print(data)

    listener = Listener.start(n_txs, ln, output)
    print(f"Start {n_txs} simulations")

    acc = n_txs
    while acc > 0:
        nodes = list(ln.nodes)
        source = choice(nodes)  # A

        nodes.remove(source)
        dest = choice(nodes)  # H

        #paths = compute_cheapest_paths(source, dest, ln)
        paths = heuristic_paths(source, dest, ln, additional_hops=0)
        if len(paths) == 0:
            print(f"WARNING: No path from {source} to {dest}")
            listener.tell(NotifyNoPath)
            continue
        path = paths.pop(0)

        amount = randint(min_amount, max_amount)

        tx = Tx(path, paths, amount)
        ref(ln, source).tell(tx)

        acc -= 1
