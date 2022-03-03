import json
from random import randint

import networkx as nx

from lightning_network.node import Node


def generate_network_old(filename: str) -> nx.DiGraph:
    ln = nx.DiGraph()

    with open(filename) as f:
        data = json.loads(f.read())
        for channel_data in data["channels"]:
            source = channel_data["source"]
            if not ln.has_node(source):
                ln.add_node(source, ref=Node.start(source, ln))

            dest = channel_data["destination"]
            if not ln.has_node(dest):
                ln.add_node(dest, ref=Node.start(dest, ln))

            satoshis = channel_data["satoshis"]
            value = int(randint(10, 90) / 100 * satoshis)

            ln.add_edge(source, dest,
                        id=channel_data["short_channel_id"],
                        satoshis=satoshis,
                        base_fee_millisatoshi=channel_data["base_fee_millisatoshi"],
                        fee_per_millionth=channel_data["fee_per_millionth"],
                        funds=value,
                        budget=value)
            ln.add_edge(dest, source,
                        id=channel_data["short_channel_id"],
                        satoshis=satoshis,
                        base_fee_millisatoshi=channel_data["base_fee_millisatoshi"],
                        fee_per_millionth=channel_data["fee_per_millionth"],
                        funds=satoshis - value,
                        budget=satoshis - value)

    for node, value in nx.betweenness_centrality(ln).items():
        ln.nodes[node]["betweeness"] = value

    return ln

def generate_network(filename: str) -> nx.DiGraph:
    ln = nx.DiGraph()

    with open(filename) as f:
        data = json.loads(f.read())
        for channel_data in data["channels"]:
            source = channel_data["node1_pub"]
            if not ln.has_node(source):
                ln.add_node(source, ref=Node.start(source, ln))

            dest = channel_data["node2_pub"]
            if not ln.has_node(dest):
                ln.add_node(dest, ref=Node.start(dest, ln))

            satoshis = int(channel_data["capacity"])
            value = int(randint(10, 90) / 100 * satoshis)

            node1_base = 1000
            node1_var = 0
            if "node1_policy" in channel_data:
                if channel_data["node1_policy"] != None:
                    node1_base = int(channel_data["node1_policy"]["fee_base_msat"])
                    node1_var = int(channel_data["node1_policy"]["fee_rate_milli_msat"])

            node2_base = 1000
            node2_var = 0
            if "node2_policy" in channel_data:
                if channel_data["node2_policy"] != None:
                    node2_base = int(channel_data["node2_policy"]["fee_base_msat"])
                    node2_var = int(channel_data["node2_policy"]["fee_rate_milli_msat"])


            ln.add_edge(source, dest,
                        id=channel_data["channel_id"],
                        satoshis=satoshis,
                        base_fee_millisatoshi=node1_base,
                        fee_per_millionth=node1_base,
                        funds=value,
                        budget=value)
            ln.add_edge(dest, source,
                        id=channel_data["channel_id"],
                        satoshis=satoshis,
                        base_fee_millisatoshi=node2_base,
                        fee_per_millionth=node2_var,
                        funds=satoshis - value,
                        budget=satoshis - value)

    print(f"Data loaded successfully ({len(ln.nodes)})")
    for node, value in nx.betweenness_centrality(ln).items():
        ln.nodes[node]["betweeness"] = value
    print("Data computed successfully")

    return ln
