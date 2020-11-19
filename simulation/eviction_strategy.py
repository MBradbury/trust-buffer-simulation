from __future__ import annotations

import numpy as np

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

    def choose_common(self, items: List, buffers: AgentBuffers):
        pass

    def choose_crypto(self, items: List[CryptoItem], buffers: AgentBuffers) -> Optional[CryptoItem]:
        return self.choose_common(items, buffers)
    def choose_trust(self, items: List[TrustItem], buffers: AgentBuffers) -> Optional[TrustItem]:
        return self.choose_common(items, buffers)
    def choose_reputation(self, items: List[ReputationItem], buffers: AgentBuffers) -> Optional[ReputationItem]:
        return self.choose_common(items, buffers)
    def choose_stereotype(self, items: List[StereotypeItem], buffers: AgentBuffers) -> Optional[StereotypeItem]:
        return self.choose_common(items, buffers)

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

    def choose_common(self, items: List, buffers: AgentBuffers):
        return self.sim.rng.choice(items)

class FIFOEvictionStrategy(EvictionStrategy):
    short_name = "FIFO"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: List, buffers: AgentBuffers):
        return min(items, key=lambda x: x.eviction_data)

class LRUEvictionStrategy(EvictionStrategy):
    short_name = "LRU"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: List, buffers: AgentBuffers):
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = self.sim.current_time

class MRUEvictionStrategy(EvictionStrategy):
    short_name = "MRU"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: List, buffers: AgentBuffers):
        return max(items, key=lambda x: x.eviction_data)

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = self.sim.current_time

class Chen2016EvictionStrategy(EvictionStrategy):
    """
    Implementation of strategy described in Section 4.4 of
    Chen, I.; Guo, J. & Bao, F.
    Trust Management for SOA-Based IoT and Its Application to Service Composition 
    IEEE Transactions on Services Computing, 2016, 9, 482-495
    """
    short_name = "Chen2016"

    omega = 0.5

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def choose_trust(self, items: List[TrustItem], buffers: AgentBuffers) -> Optional[TrustItem]:
        # Remove the earliest interacting node with a trust value below the median
        # Can't do below the median, need to also include it as otherwise there
        # may be no items to select from
        quantile = np.quantile([item.brs_trust() for item in items], self.omega)

        filtered_items = [item for item in items if item.brs_trust() <= quantile]

        try:
            return min(filtered_items, key=lambda x: x.eviction_data)
        except ValueError:
            # Fallback to LRU
            return min(items, key=lambda x: x.eviction_data)

    def choose_common(self, items: List, buffers: AgentBuffers):
        # Do LRU for everything else
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = self.sim.current_time

class FiveBandEvictionStrategy(EvictionStrategy):
    short_name = "FiveBand"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def choose_trust(self, items: List[TrustItem], buffers: AgentBuffers) -> Optional[TrustItem]:
        item_trust = [item.brs_trust() for item in items]

        quantile = np.quantile(item_trust, [0.2, 0.4, 0.6, 0.8, 1.0])

        # Keep the 20% best and worst nodes as they provide useful information
        # Keep the middle 20% nodes as they may not have had a chance to stabilise
        # Consider removing the inbetween nodes that are neither very good or very bad

        print("quantile", quantile)

        low, lowmid, mid, highmid, high = quantile

        filtered_items = [
            item
            for item in items
            if low < item.brs_trust() <= lowmid
            or mid < item.brs_trust() <= highmid
        ]

        try:
            return min(filtered_items, key=lambda x: x.eviction_data)
        except ValueError:
            # No items in that range, so fall back to Chen2016
            quantile = np.quantile(item_trust, 0.5)

            filtered_items = [item for item in items if item.brs_trust() <= quantile]

            try:
                return min(filtered_items, key=lambda x: x.eviction_data)
            except ValueError:
                # Fallback to LRU
                return min(items, key=lambda x: x.eviction_data)

    def choose_common(self, items: List, buffers: AgentBuffers):
        # Do LRU for everything else
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = self.sim.current_time
