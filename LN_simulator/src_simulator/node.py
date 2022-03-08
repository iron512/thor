import threading
from types import TracebackType
from typing import Type

import networkx as nx
from pykka import ThreadingActor, ActorRef, ActorRegistry

from src_simulator.algorithms import calculate_total_fee
from src_simulator.listener import Listener
from src_simulator.messages import TxPrecommit, TxAbort, TxReq, Tx, NotifyCommit, NotifyAbort, TxCommit
from src_simulator.worker import Worker


class Node(ThreadingActor):
    class Retry(Tx):
        pass

    def __init__(self, name: str, nl: nx.DiGraph):
        """
        Constructs a lightning network node
        :param name: name of the node
        :param nl: network topology
        """
        super().__init__()

        self.name = name
        self.ln = nl

        self.backlog: list[Tx] = []

        self.wait_for_tx()

    def __str__(self):
        return self.name

    def wait_for_tx(self):
        """
        Waits for the node to generate new transactions
        """

        def wait_for_tx(msg):
            if isinstance(msg, Tx):
                self.issue_tx(msg.next_hops, msg.paths, msg.amount)
            elif isinstance(msg, TxReq):
                self.delegate(msg.sender, msg.next_hops, msg.amount)

        # noinspection PyAttributeOutsideInit
        self.on_receive = wait_for_tx

    def wait_for_retry(self):
        """
        Defers any new transaction the node generates, processes only retries
        """

        def wait_for_retry(msg):
            if isinstance(msg, Node.Retry):
                self.issue_tx(msg.next_hops, msg.paths, msg.amount)
            elif isinstance(msg, Tx):
                self.backlog.append(msg)
            elif isinstance(msg, TxReq):
                self.delegate(msg.sender, msg.next_hops, msg.amount)

        # noinspection PyAttributeOutsideInit
        self.on_receive = wait_for_retry

    def process_backlog_and_wait(self):
        if len(self.backlog) > 0:
            tx = self.backlog.pop(0)
            self.issue_tx(tx.next_hops, tx.paths, tx.amount)
        else:
            self.wait_for_tx()

    def wait_for_precommit_or_abort(self, path: list[str], paths: list[list[str]], amount: int):
        def wait_for_precommit_or_abort(msg):
            if isinstance(msg, TxPrecommit):
                self.on_precommit(msg.sender, path)
            elif isinstance(msg, TxAbort):
                self.on_abort(paths, amount)
            elif isinstance(msg, Tx):
                self.backlog.append(msg)
            elif isinstance(msg, TxReq):
                self.delegate(msg.sender, msg.next_hops, msg.amount)

        # noinspection PyAttributeOutsideInit
        self.on_receive = wait_for_precommit_or_abort

    def schedule_retry(self, tx: Tx, s: float):
        """
        Schedules the execution of a new transaction in the future
        :param tx: transaction to scheduled
        :param s: seconds to wait before executing the schedule
        """
        threading.Timer(s, lambda: self.actor_ref.tell(tx)).start()
        self.wait_for_retry()

    def issue_tx(self, path: list[str], paths: list[list[str]], amount: int):
        dest = path[-1]
        fee = calculate_total_fee(self.ln, [self.name] + path)
        # print(f"{self}: tx to {dest}, $ {amount}, fee is $ {fee}, path is {path}")

        worker = Worker.start(self.name, self.ln)
        req = TxReq(self.actor_ref, path, amount + fee)
        worker.tell(req)

        self.wait_for_precommit_or_abort(path, paths, amount)

    def on_precommit(self, sender: ActorRef, path: list[str]):
        commit = TxCommit(self.actor_ref)
        sender.tell(commit)

        notify = NotifyCommit(str(self), path)
        self.notify_listener(notify)

        self.process_backlog_and_wait()

    def on_abort(self, paths: list[list[str]], amount: int):
        if len(paths) > 0:
            retry = Node.Retry(paths.pop(0), paths, amount)
            self.schedule_retry(retry, 0.05)
        else:
            notify = NotifyAbort(str(self))
            self.notify_listener(notify)

            self.process_backlog_and_wait()

    def delegate(self, sender: ActorRef, path: list[str], amount: int):
        worker = Worker.start(self.name, self.ln)
        req = TxReq(sender, path, amount)
        worker.tell(req)

    def on_failure(self, exception_type: Type[BaseException],
                   exception_value: BaseException,
                   traceback: TracebackType) -> None:
        print(f"{self.name}: failure: {exception_type.__name__}: {exception_value}")

    def notify_listener(self, msg: NotifyCommit | NotifyAbort):
        listener = ActorRegistry.get_by_class(Listener)
        if len(listener) > 0:
            listener[0].tell(msg)
