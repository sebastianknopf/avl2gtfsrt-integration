from abc import ABC, abstractmethod

from avl2gtfsrt.integration.model.types import AvlPosition


class BaseAdapter(ABC):

    def __init__(self, config: dict) -> None:
        self.interval = config['interval']

    @abstractmethod
    def get_current_positions(self) -> list[AvlPosition]:
        pass