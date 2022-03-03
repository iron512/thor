import json

import networkx as nx


def generate_network_old(filename: str) -> nx.Graph:
    ln = nx.Graph()

    with open(filename) as f:
        data = json.loads(f.read())
        for channel_data in data["channels"]:
            source = channel_data["source"]
            dest = channel_data["destination"]
            ln.add_edge(source, dest)

    return ln

def generate_network(filename: str) -> nx.Graph:
    ln = nx.Graph()

    with open(filename) as f:
        data = json.loads(f.read())
        for channel_data in data["channels"]:
            source = channel_data["node1_pub"]
            dest = channel_data["node2_pub"]
            ln.add_edge(source, dest)

    return ln


def rank_nodes_by_betweeness_centrality(ln: nx.Graph) -> list[(str, float)]:
    print("Calculating betweenness centrality...")

    # Dictionary of nodes with betweenness centrality as the value.
    node_and_values = nx.betweenness_centrality(ln)

    # Convert to list
    node_and_values = list(node_and_values.items())

    # Sort by betweenness value
    node_and_values.sort(key=lambda tup: tup[1], reverse=True)

    return node_and_values

def rank_nodes_by_closeness_centrality(ln: nx.Graph) -> list[(str, float)]:
    print("Calculating closeness centrality...")

    # Dictionary of nodes with betweenness centrality as the value.
    node_and_values = nx.closeness_centrality(ln)

    # Convert to list
    node_and_values = list(node_and_values.items())

    # Sort by betweenness value
    node_and_values.sort(key=lambda tup: tup[1], reverse=True)

    return node_and_values


def rank_nodes_by_degree(ln: nx.Graph) -> list[(str, float)]:
    print("Calculating degree...")

    # noinspection PyTypeChecker
    node_and_degrees = list(ln.degree)
    node_and_degrees.sort(key=lambda tup: tup[1], reverse=True)
    return node_and_degrees


def select_nodes_by_percentage(nodes_and_values: list[()], percentage: int, ln: nx.Graph) -> (list[str], int):
    malicious_nodes = []
    selected_edges = set()
    while (len(selected_edges) / len(ln.edges) * 100) < percentage and len(nodes_and_values) > 0:
        node, value = nodes_and_values.pop(0)
        malicious_nodes.append(node)
        for edge in ln.edges(node):
            selected_edges.add(edge)
    return malicious_nodes, len(selected_edges)


def is_path_controlled(path: list[str], malicious_nodes: list[str]):
    if path[0] in malicious_nodes or path[-1] in malicious_nodes:
        return True

    indexes = set()
    for i in range(1, len(path) - 1):
        if path[i] in malicious_nodes:
            indexes.add(i - 1)
            indexes.add(i)
            indexes.add(i + 1)
    return len(indexes) == len(path)


def count_controlled_paths(paths: list[list[str]], malicious_nodes: list[str]):
    count = 0
    for path in paths:
        if is_path_controlled(path, malicious_nodes):
            count += 1
    return count


def read_paths(file: str) -> list[list[str]]:
    paths = []
    with open(file) as f:
        lines = f.readlines()
        for line in lines:
            path = line.replace("\n", "").split(" ")
            paths.append(path)
    return paths


ln = generate_network("networks/snap18042019.json")

# Rank nodes depending on a metric
by_betweeness_centrality = rank_nodes_by_betweeness_centrality(ln)
by_closeness_centrality = rank_nodes_by_closeness_centrality(ln)
by_degree = rank_nodes_by_degree(ln)


#files = ["std/1_std.txt","std/2_std.txt","std/3_std.txt"]
#files = ["heur/1_heur.txt","heur/2_heur.txt","heur/3_heur.txt"]
files = ["1hop/1_1hop.txt","1hop/2_1hop.txt","1hop/3_1hop.txt",
        "2hops/1_2hops.txt","2hops/2_2hops.txt","2hops/3_2hops.txt",
        "4hops/1_4hops.txt","4hops/2_4hops.txt","4hops/3_4hops.txt"]


print(f"There are {len(ln.nodes)} nodes and {len(ln.edges)} edges.")

for file in files:
    paths = read_paths(file)
    print()
    print(f"Crunching data for {file}")
    
    print("Betweeness centrality")

    bc_10_nodes, bc_10_edges = select_nodes_by_percentage(by_betweeness_centrality.copy(), 10, ln)
    bc_10_controlled_nodes_count = count_controlled_paths(paths, bc_10_nodes)
    print(f"10%: "
          f"selected nodes are {len(bc_10_nodes)} ({bc_10_edges} edges), "
          f"controlled paths are {bc_10_controlled_nodes_count} "
          f"({round(bc_10_controlled_nodes_count / len(paths) * 100, 2)}%)")

    bc_20_nodes, bc_20_edges = select_nodes_by_percentage(by_betweeness_centrality.copy(), 20, ln)
    bc_20_controlled_nodes_count = count_controlled_paths(paths, bc_20_nodes)
    print(f"20%: "
          f"selected nodes are {len(bc_20_nodes)} ({bc_20_edges} edges), "
          f"controlled paths are {bc_20_controlled_nodes_count} "
          f"({round(bc_20_controlled_nodes_count / len(paths) * 100, 2)}%)")

    bc_40_nodes, bc_40_edges = select_nodes_by_percentage(by_betweeness_centrality.copy(), 40, ln)
    bc_40_controlled_nodes_count = count_controlled_paths(paths, bc_40_nodes)
    print(f"40%: "
          f"selected nodes are {len(bc_40_nodes)} ({bc_40_edges} edges), "
          f"controlled paths are {bc_40_controlled_nodes_count} "
          f"({round(bc_40_controlled_nodes_count / len(paths) * 100, 2)}%)")

    bc_60_nodes, bc_60_edges = select_nodes_by_percentage(by_betweeness_centrality.copy(), 60, ln)
    bc_60_controlled_nodes_count = count_controlled_paths(paths, bc_60_nodes)
    print(f"60%: "
          f"selected nodes are {len(bc_60_nodes)} ({bc_60_edges} edges), "
          f"controlled paths are {bc_60_controlled_nodes_count} "
          f"({round(bc_60_controlled_nodes_count / len(paths) * 100, 2)}%)")

    print("By degree")

    d_10_nodes, d_10_edges = select_nodes_by_percentage(by_degree.copy(), 10, ln)
    d_10_controlled_paths_count = count_controlled_paths(paths, d_10_nodes)
    print(f"10%: "
          f"selected nodes are {len(d_10_nodes)}, ({d_10_edges} edges)",
          f"controlled paths are {d_10_controlled_paths_count} "
          f"({round(d_10_controlled_paths_count / len(paths) * 100, 2)}%)")

    d_20_nodes, d_20_edges = select_nodes_by_percentage(by_degree.copy(), 20, ln)
    d_20_controlled_paths_count = count_controlled_paths(paths, d_20_nodes)
    print(f"20%: "
          f"selected nodes are {len(d_20_nodes)}, ({d_20_edges} edges)",
          f"controlled paths are {d_20_controlled_paths_count} "
          f"({round(d_20_controlled_paths_count / len(paths) * 100, 2)}%)")

    d_40_nodes, d_40_edges = select_nodes_by_percentage(by_degree.copy(), 40, ln)
    d_40_controlled_paths_count = count_controlled_paths(paths, d_40_nodes)
    print(f"40%: "
          f"selected nodes are {len(d_40_nodes)}, ({d_40_edges} edges)",
          f"controlled paths are {d_40_controlled_paths_count} "
          f"({round(d_40_controlled_paths_count / len(paths) * 100, 2)}%)")

    d_60_nodes, d_60_edges = select_nodes_by_percentage(by_degree.copy(), 60, ln)
    d_60_controlled_paths_count = count_controlled_paths(paths, d_60_nodes)
    print(f"60%: "
          f"selected nodes are {len(d_60_nodes)}, ({d_60_edges} edges)",
          f"controlled paths are {d_60_controlled_paths_count} "
          f"({round(d_60_controlled_paths_count / len(paths) * 100, 2)}%)")

    print("Closeness centrality")

    cc_10_nodes, cc_10_edges = select_nodes_by_percentage(by_closeness_centrality.copy(), 10, ln)
    cc_10_controlled_nodes_count = count_controlled_paths(paths, cc_10_nodes)
    print(f"10%: "
          f"selected nodes are {len(cc_10_nodes)} ({cc_10_edges} edges), "
          f"controlled paths are {cc_10_controlled_nodes_count} "
          f"({round(cc_10_controlled_nodes_count / len(paths) * 100, 2)}%)")

    cc_20_nodes, cc_20_edges = select_nodes_by_percentage(by_closeness_centrality.copy(), 20, ln)
    cc_20_controlled_nodes_count = count_controlled_paths(paths, cc_20_nodes)
    print(f"20%: "
          f"selected nodes are {len(cc_20_nodes)} ({cc_20_edges} edges), "
          f"controlled paths are {cc_20_controlled_nodes_count} "
          f"({round(cc_20_controlled_nodes_count / len(paths) * 100, 2)}%)")

    cc_40_nodes, cc_40_edges = select_nodes_by_percentage(by_closeness_centrality.copy(), 40, ln)
    cc_40_controlled_nodes_count = count_controlled_paths(paths, cc_40_nodes)
    print(f"40%: "
          f"selected nodes are {len(cc_40_nodes)} ({cc_40_edges} edges), "
          f"controlled paths are {cc_40_controlled_nodes_count} "
          f"({round(cc_40_controlled_nodes_count / len(paths) * 100, 2)}%)")

    cc_60_nodes, cc_60_edges = select_nodes_by_percentage(by_closeness_centrality.copy(), 60, ln)
    cc_60_controlled_nodes_count = count_controlled_paths(paths, cc_60_nodes)
    print(f"60%: "
          f"selected nodes are {len(cc_60_nodes)} ({cc_60_edges} edges), "
          f"controlled paths are {cc_60_controlled_nodes_count} "
          f"({round(cc_60_controlled_nodes_count / len(paths) * 100, 2)}%)")
