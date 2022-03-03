from os import listdir

from pkg_resources import resource_filename

TOPOLOGY_DIR = resource_filename("lightning_network", "topologies")


def available_topologies():
    return listdir(TOPOLOGY_DIR)
