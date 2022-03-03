import time

import networkx as nx
from pykka import ThreadingActor, ActorRegistry

from src.messages import NotifyCommit, NotifyAbort


class Listener(ThreadingActor):
    def __init__(self, n_txs: int, ln: nx.DiGraph, output: str):
        """
        Creates a listener which stops the simulation after receiving the specified number of commit or abort messages
        :param n_txs: number of commit or abort messages to receive before stopping the simulation
        :param ln: network topology
        """
        super().__init__()

        self.ln = ln
        self.paths = []
        self.output = output

        self.n_txs = n_txs
        self.n_commit = 0
        self.n_abort = 0

    def n_tx_left(self):
        return self.n_txs - self.n_commit - self.n_abort

    def on_receive(self, msg):
        if isinstance(msg, NotifyCommit):
            self.n_commit += 1
            print(f"{msg.node} committed. "
                  f"{self.n_commit} commits, {self.n_abort} aborts, "
                  f"{self.n_commit / (self.n_commit + self.n_abort) * 100:.0f}% success, "
                  f"{self.n_tx_left()} left")

            self.paths.append([msg.node] + msg.path)

            if self.n_tx_left() == 0:
                self.write_paths_to_file()
                self.check_invariant()
                self.stop_all()
        elif isinstance(msg, NotifyAbort):
            self.n_abort += 1
            print(f"{msg.node} aborted. "
                  f"{self.n_commit} commits, {self.n_abort} aborts, "
                  f"{self.n_commit / (self.n_commit + self.n_abort) * 100:.0f}% success, "
                  f"{self.n_tx_left()} left")
            if self.n_tx_left() == 0:
                self.write_paths_to_file()
                self.check_invariant()
                self.stop_all()

    def stop_all(self):
        # Do not use ActorRegistry.stop_all()

        from src.node import Node
        for node in ActorRegistry.get_by_class(Node):
            node.stop(False)

        from src.worker import Worker
        for worker in ActorRegistry.get_by_class(Worker):
            worker.stop(False)

        self.stop()

    def check_invariant(self):
        time.sleep(0.5)
        for edge in self.ln.edges:
            funds = self.ln[edge[0]][edge[1]]["funds"]
            budget = self.ln[edge[0]][edge[1]]["budget"]
            if funds != budget:
                print(f"Edge {edge}: Funds ({funds}) differs from budget ({budget})")

    def write_paths_to_file(self):
        if self.output != None:
            with open(self.output, "w") as f:
                for path in self.paths:
                    line = " ".join(path)
                    f.write(line + "\n")
