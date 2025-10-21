
from avl2gtfsrt.integration.adapter.baseadapter import BaseAdapter
from avl2gtfsrt.integration.model.types import AvlPosition

class PajGpsAdapter(BaseAdapter):
    
    def __init__(self, config: dict) -> None:
        super().__init__(config)

    def get_current_positions(self) -> list[AvlPosition]:
        return list()