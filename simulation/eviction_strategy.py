from __future__ import annotations

class EvictionStrategy:
    def __init__(self, sim: Simulation):
        self.sim = sim

    def add_common(self, item):
        pass

    def add_crypto(self, item: CryptoItem):
        return self.add_common(item)
    def add_trust(self, item: TrustItem):
        return self.add_common(item)
    def add_reputation(self, item: ReputationItem):
        return self.add_common(item)
    def add_stereotype(self, item: StereotypeItem):
        return self.add_common(item)

    def choose_common(self, items: List):
        pass

    def choose_crypto(self, items: List[CryptoItem]) -> Optional[CryptoItem]:
        return self.choose_common(items)
    def choose_trust(self, items: List[TrustItem]) -> Optional[TrustItem]:
        return self.choose_common(items)
    def choose_reputation(self, items: List[ReputationItem]) -> Optional[ReputationItem]:
        return self.choose_common(items)
    def choose_stereotype(self, items: List[StereotypeItem]) -> Optional[StereotypeItem]:
        return self.choose_common(items)

    def use_common(self, item):
        pass

    def use_crypto(self, item: CryptoItem):
        return self.use_common(item)
    def use_trust(self, item: TrustItem):
        return self.use_common(item)
    def use_reputation(self, item: ReputationItem):
        return self.use_common(item)
    def use_stereotype(self, item: StereotypeItem):
        return self.use_common(item)

class RandomEvictionStrategy(EvictionStrategy):
    short_name = "Random"

    def choose_common(self, items: List):
        return self.sim.rng.choice(items)

class FIFOEvictionStrategy(EvictionStrategy):
    short_name = "FIFO"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: List):
        return min(items, key=lambda x: x.eviction_data)

class LRUEvictionStrategy(EvictionStrategy):
    short_name = "LRU"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: List):
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = self.sim.current_time

class MRUEvictionStrategy(EvictionStrategy):
    short_name = "MRU"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: List):
        return max(items, key=lambda x: x.eviction_data)

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = self.sim.current_time
