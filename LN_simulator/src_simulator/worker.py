from types import TracebackType
from typing import Type

import networkx as nx
from pykka import ThreadingActor, ActorRef, ActorDeadError

from src_simulator.algorithms import calculate_fee, allocate_budget, ref, decrement_funds, \
    increment_funds, deallocate_budget
from src_simulator.messages import TxReq, TxCommit, TxPrecommit, TxAbort


class Worker(ThreadingActor):
    def __init__(self, parent: str, ln: nx.Graph):
        """
        Constructs a worker child to which the parent node delegates the work of a transaction
        :param parent: name of the node which is delegating work
        :param ln: network topology
        """
        super().__init__()

        self.name = parent
        self.ln = ln

        self.wait_for_request()

    def __str__(self):
        return self.name

    def wait_for_request(self):
        """
        Waits for the parent to delegate the work of a transaction.
        Next states: wait_for_tx_rep or stop
        """

        def wait_for_tx_req(msg):
            if isinstance(msg, TxReq):
                self.on_request(msg.sender, msg.next_hops, msg.amount)

        # noinspection PyAttributeOutsideInit
        self.on_receive = wait_for_tx_req

    def wait_for_precommit_or_abort(self, prev_hop: ActorRef, next_hop: str, amount: int):
        """
        Waits for a precommit or abort message to arrive and processes it
        Next states: wait_for_decision or stop
        """

        def wait_for_precommit_or_abort(msg):
            if isinstance(msg, TxPrecommit):
                self.on_precommit(prev_hop, next_hop, msg.sender, amount)
            elif isinstance(msg, TxAbort):
                self.on_abort(prev_hop, next_hop, amount)

        # noinspection PyAttributeOutsideInit
        self.on_receive = wait_for_precommit_or_abort

    def wait_for_decision(self, prev_hop: ActorRef, next_hop: str, forward_to: ActorRef, amount: int):
        """
        Wait for the decision (either commit or abort) to arrive and processes it.
        Next state: stop
        """

        def wait_for_decision(msg):
            if isinstance(msg, TxCommit):
                self.on_commit(next_hop, forward_to, amount)
            elif isinstance(msg, TxAbort):
                self.on_abort(prev_hop, next_hop, amount)

        # noinspection PyAttributeOutsideInit
        self.on_receive = wait_for_decision

    def on_request(self, prev_hop: ActorRef, next_hops: list[str], amount: int):
        if len(next_hops) == 0:
            # This is the last node.
            # Since it can only receive money, it can stop right away.
            precommit = TxPrecommit(self.actor_ref)
            prev_hop.tell(precommit)

            self.stop()
        else:
            # There is at least one hop next.
            # Check if there is enough budget to accommodate the request.
            # If yes, provisionally allocate budget for the request, then forward it and wait for a response.
            # If not, tell the predecessor to abort and stop.
            next_hop = next_hops[0]
            fee = calculate_fee(self.ln, self.name, next_hop)

            if allocate_budget(self.ln, self.name, next_hop, amount, fee):
                req = TxReq(self.actor_ref, next_hops[1:], amount - fee)
                ref(self.ln, next_hop).tell(req)

                self.wait_for_precommit_or_abort(prev_hop, next_hop, amount)
            else:
                abort = TxAbort(self.actor_ref)
                prev_hop.tell(abort)

                self.stop()

    def on_precommit(self, prev_hop: ActorRef, next_hop: str, forward_to: ActorRef, amount):
        precommit = TxPrecommit(self.actor_ref)
        prev_hop.tell(precommit)

        self.wait_for_decision(prev_hop, next_hop, forward_to, amount)

    def on_abort(self, prev_hop: ActorRef, next_hop: str, amount: int):
        deallocate_budget(self.ln, self.name, next_hop, amount)

        abort = TxAbort(self.actor_ref)
        prev_hop.tell(abort)

        self.stop()

    def on_commit(self, next_hop: str, forward_to: ActorRef, amount: int):
        decrement_funds(self.ln, self.name, next_hop, amount)
        increment_funds(self.ln, next_hop, self.name, amount)

        try:
            commit = TxCommit(self.actor_ref)
            forward_to.tell(commit)
        except ActorDeadError:
            # Second to last node forwards the commit to the last node, which is not there anymore
            pass

        self.stop()

    def on_failure(self, exception_type: Type[BaseException],
                   exception_value: BaseException,
                   traceback: TracebackType) -> None:
        print(f"{self.name}: failure: {exception_type.__name__}: {exception_value}")
