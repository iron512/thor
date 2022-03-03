import threading

import networkx as nx
from pykka import ActorRef

lock = threading.Lock()


def compute_cheapest_paths(source: str, dest: str, ln: nx.Graph, max_paths=10) -> list[list[str]]:
    """
    Computes the cheapest paths between source and destination nodes
    :param source: source of the source node
    :param dest: source of the destination node
    :param ln: network topology
    :param max_paths: maximum number of paths to compute
    :return: the computed shortest paths. The first node of each shortest path is the node immediately succeeding
    the source node
    """
    paths: list[list[str]] = []
    if nx.has_path(ln, source, dest):
        generator = nx.shortest_simple_paths(ln, source, dest, weight="base_fee_millisatoshi")
        try:
            while len(paths) < max_paths:
                path = next(generator)
                paths.append(path[1:])  # remove the source node
        except StopIteration:
            pass
    return paths


def heuristic_paths(source: str, dest: str, ln: nx.Graph, max_paths=10, additional_hops=2) -> list[list[str]]:
    cutoff = 80

    paths: list[list[str]] = []
    if nx.has_path(ln, source, dest):
        generator = nx.shortest_simple_paths(ln, source, dest, weight="base_fee_millisatoshi")
        min_path_len = len(next(generator)) + additional_hops

        try:
            while len(paths) < max_paths and cutoff > 0:
                path = next(generator)
                if len(path) >= min_path_len:
                    paths.append(path[1:])  # remove the source node
                cutoff -= 1
        except StopIteration:
            pass

    if len(paths) > 0:
        paths.sort(key=lambda path: sum(ln.nodes[node]["betweeness"] for node in path) / len(path))

    return paths


def calculate_fee(ln: nx.Graph, source: str, dest: str) -> int:
    base_fee_millisatoshi = ln.get_edge_data(source, dest)["base_fee_millisatoshi"]
    return int(base_fee_millisatoshi / 1000)


def calculate_total_fee(ln: nx.Graph, path: list[str]) -> int:
    return sum(calculate_fee(ln, source, dest) for source, dest in zip(path, path[1:-1]))


def ref(ln: nx.Graph, name: str) -> ActorRef:
    """
    Convenience method for retrieving the ActorRef of a given node in the lightning network
    :param ln: the lightning network
    :param name: name of the node in the lightning network for which to retrieve the ActorRef
    :return: the ActorRef for the specified node in the lightning network
    """
    return ln.nodes[name]["ref"]


def decrement_funds(ln: nx.Graph, source: str, dest: str, amount: int):
    with lock:
        ln[source][dest]["funds"] -= amount


def increment_funds(ln: nx.Graph, source: str, dest: str, amount: int):
    with lock:
        ln[source][dest]["funds"] += amount
        ln[source][dest]["budget"] += amount


def allocate_budget(ln: nx.Graph, source: str, dest: str, amount: int, fee: int) -> bool:
    with lock:
        if amount + fee < ln.get_edge_data(source, dest)["budget"]:
            ln[source][dest]["budget"] -= amount
            return True
        return False


def deallocate_budget(ln: nx.Graph, source: str, dest: str, amount: int):
    with lock:
        ln[source][dest]["budget"] += amount
