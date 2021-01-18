import enum


class BasestationInterface:
    class Action(enum.Enum):
        ON = enum.auto()
        OFF = enum.auto()

    def __init__(self, config):
        self.config = config

    def action(self, action):
        raise NotImplementedError()
