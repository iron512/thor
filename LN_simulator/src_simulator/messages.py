from pykka import ActorRef


class Tx:
    def __init__(self, next_hops: list[str], paths: list[list[str]], amount: int):
        self.next_hops = next_hops
        self.paths = paths
        self.amount = amount


class TxReq:
    def __init__(self, ref: ActorRef, next_hops: list[str], amount: int):
        self.sender = ref
        self.next_hops = next_hops
        self.amount = amount


class TxPrecommit:
    def __init__(self, ref: ActorRef):
        self.sender = ref


class TxCommit:
    def __init__(self, sender: ActorRef):
        self.sender = sender


class TxAbort:
    def __init__(self, sender: ActorRef):
        self.sender = sender


class NotifyCommit:
    def __init__(self, node: str, path: list[str]):
        self.node = node
        self.path = path


class NotifyAbort:
    def __init__(self, node: str):
        self.node = node


class NotifyNoPath:
    pass
