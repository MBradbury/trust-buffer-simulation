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

    def choose_common(self, items: List, buffers: AgentBuffers, new_item):
        pass

    def choose_crypto(self, items: List[CryptoItem], buffers: AgentBuffers, new_item: CryptoItem) -> Optional[CryptoItem]:
        return self.choose_common(items, buffers, new_item)
    def choose_trust(self, items: List[TrustItem], buffers: AgentBuffers, new_item: TrustItem) -> Optional[TrustItem]:
        return self.choose_common(items, buffers, new_item)
    def choose_reputation(self, items: List[ReputationItem], buffers: AgentBuffers, new_item: ReputationItem) -> Optional[ReputationItem]:
        return self.choose_common(items, buffers, new_item)
    def choose_stereotype(self, items: List[StereotypeItem], buffers: AgentBuffers, new_item: StereotypeItem) -> Optional[StereotypeItem]:
        return self.choose_common(items, buffers, new_item)

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

class NoneEvictionStrategy(EvictionStrategy):
    short_name = "None"

    def choose_common(self, items: List, buffers: AgentBuffers, new_item):
        return None

class RandomEvictionStrategy(EvictionStrategy):
    short_name = "Random"

    def choose_common(self, items: List, buffers: AgentBuffers, new_item):
        return self.sim.rng.choice(items)

class FIFOEvictionStrategy(EvictionStrategy):
    short_name = "FIFO"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: List, buffers: AgentBuffers, new_item):
        return min(items, key=lambda x: x.eviction_data)

class LRUEvictionStrategy(EvictionStrategy):
    short_name = "LRU"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: List, buffers: AgentBuffers, new_item):
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = self.sim.current_time

class LRU2EvictionStrategy(EvictionStrategy):
    short_name = "LRU2"

    def add_common(self, item):
        item.eviction_data = (self.sim.current_time, self.sim.current_time)

    def choose_common(self, items: List, buffers: AgentBuffers, new_item):
        return min(items, key=lambda x: x.eviction_data[1])

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = (self.sim.current_time, item.eviction_data[0])

class MRUEvictionStrategy(EvictionStrategy):
    short_name = "MRU"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: List, buffers: AgentBuffers, new_item):
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

    def choose_trust(self, items: List[TrustItem], buffers: AgentBuffers, new_item) -> Optional[TrustItem]:
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

    def choose_common(self, items: List, buffers: AgentBuffers, new_item):
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

    def choose_trust(self, items: List[TrustItem], buffers: AgentBuffers, new_item: TrustItem) -> Optional[TrustItem]:
        item_trust = [item.brs_trust() for item in items]

        quantile = np.quantile(item_trust, [0.2, 0.4, 0.6, 0.8, 1.0])

        # Keep the 20% best and worst nodes as they provide useful information
        # Keep the middle 20% nodes as they may not have had a chance to stabilise
        # Consider removing the inbetween nodes that are neither very good or very bad

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

    def choose_common(self, items: List, buffers: AgentBuffers, new_item):
        # Do LRU for everything else
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = self.sim.current_time


class NotInOtherEvictionStrategy(EvictionStrategy):
    short_name = "NotInOther"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def _lru(self, items):
        if not items:
            return None

        return min(items, key=lambda x: x.eviction_data)

    def choose_crypto(self, items: List[CryptoItem], buffers: AgentBuffers, new_item: CryptoItem) -> Optional[CryptoItem]:
        if not items:
            return None

        choices = [
            item
            for item in items
            if buffers.buffer_has_agent_count(item.agent, "TRS") == 0
        ]
        if choices:
            return self._lru(choices)

        return self._lru(items)

    def choose_trust(self, items: List[TrustItem], buffers: AgentBuffers, new_item: TrustItem) -> Optional[TrustItem]:
        if not items:
            return None

        choices = [
            item
            for item in items
            if buffers.buffer_has_agent_capability_count(item.agent, item.capability, "CRS") == 0
        ]
        if choices:
            return self._lru(choices)

        return self._lru(items)

    def choose_reputation(self, items: List[ReputationItem], buffers: AgentBuffers, new_item: ReputationItem) -> Optional[ReputationItem]:
        if not items:
            return None

        choices = [
            item
            for item in items
            if all(buffers.buffer_has_agent_capability_count(trust_item.agent, trust_item.capability, "CTS") == 0 for trust_item in item.trust_items)
        ]
        if choices:
            return self._lru(choices)

        return self._lru(items)

    def choose_stereotype(self, items: List[StereotypeItem], buffers: AgentBuffers, new_item: StereotypeItem) -> Optional[StereotypeItem]:
        if not items:
            return None

        choices = [
            item
            for item in items
            if buffers.buffer_has_agent_capability_count(item.agent, item.capability, "CTR") == 0
        ]
        if choices:
            return self._lru(choices)

        return self._lru(items)

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = self.sim.current_time


class MinNotInOtherEvictionStrategy(EvictionStrategy):
    short_name = "MinNotInOther"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def _lru(self, choices):
        if not choices:
            return None

        min_count = min(choices, key=lambda x: x[1])[1]

        selected = [item for (item, count) in choices if count == min_count]

        return min(selected, key=lambda x: x.eviction_data)

    def choose_crypto(self, items: List[CryptoItem], buffers: AgentBuffers, new_item: CryptoItem) -> Optional[CryptoItem]:
        if not items:
            return None

        choices = [
            (item, buffers.buffer_has_agent_count(item.agent, "TRS"))
            for item in items
        ]

        return self._lru(choices)

    def choose_trust(self, items: List[TrustItem], buffers: AgentBuffers, new_item: TrustItem) -> Optional[TrustItem]:
        if not items:
            return None

        choices = [
            (item, buffers.buffer_has_agent_capability_count(item.agent, item.capability, "CRS"))
            for item in items
        ]

        return self._lru(choices)

    def choose_reputation(self, items: List[ReputationItem], buffers: AgentBuffers, new_item: ReputationItem) -> Optional[ReputationItem]:
        if not items:
            return None

        choices = [
            (item, sum(buffers.buffer_has_agent_capability_count(trust_item.agent, trust_item.capability, "CTS") for trust_item in item.trust_items))
            for item in items
        ]

        return self._lru(choices)

    def choose_stereotype(self, items: List[StereotypeItem], buffers: AgentBuffers, new_item: StereotypeItem) -> Optional[StereotypeItem]:
        if not items:
            return None

        choices = [
            (item, buffers.buffer_has_agent_capability_count(item.agent, item.capability, "CTR"))
            for item in items
        ]

        return self._lru(choices)

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = self.sim.current_time


"""
class HolisticEvictionStrategy(EvictionStrategy):
    short_name = "Holistic"

    def add_common(self, item):
        item.eviction_data = self.sim.current_time

    def _lru(self, items):
        if not items:
            return None

        return min(items, key=lambda x: x.eviction_data)

    def choose_crypto(self, items: List[CryptoItem], buffers: AgentBuffers, new_item: CryptoItem) -> Optional[CryptoItem]:
        if not items:
            return None

        # Remove crypto item from those with the lowest trust value

        all_trust_values = {
            (trust_item.agent, trust_item.capability): trust_item.brs_trust()
            for trust_item in buffers.trust
        }

        trust_values = {
            item.agent: max(l) if l else float('nan')

            for item in items
            for l in [[v for ((a, c), v) in all_trust_values.items() if a == item.agent]]
        }
        min_trust_value = min(trust_values.values())
        
        # Try to only evict low trust items
        choices = [item for item in items if min_trust_value + 0.1 <= trust_values[item.agent]]
        if not choices:
            choices = items

        # Do not evict keys for highly trusted agents
        choices = [item for item in choices if trust_values[item.agent] <= 0.8]
        if not choices:
            choices = items

        return self._lru(choices)

    def choose_trust(self, items: List[TrustItem], buffers: AgentBuffers, new_item: TrustItem) -> Optional[TrustItem]:
        if not items:
            return None

        min_trust_value = min(item.brs_trust() for item in items)

        choices = [item for item in items if min_trust_value + 0.1 <= item.brs_trust()]
        if not choices:
            choices = items

        return self._lru(choices)

    def choose_reputation(self, items: List[ReputationItem], buffers: AgentBuffers, new_item: ReputationItem) -> Optional[ReputationItem]:
        if not items:
            return None

        # First try and evict items whcih we do not have other information for
        aware_crypto = {
            item.agent: buffers.find_crypto(item.agent)
            for item in items
        }
        #aware_trust = {
        #    (item.agent, item.capability): buffers.find_trust(item.agent, item.capability)
        #    for item in items
        #}
        #aware_reputation = {
        #    item.agent: buffers.find_reputation(item.agent)
        #    for item in items
        #}

        chosen = [
            item
            for item in items
            if aware_crypto[item.agent] is None
            #and aware_trust[(item.agent, item.capability)] is None
            #and aware_reputation[item.agent] is None
        ]
        if chosen:
            return self._lru(chosen)

        return self._lru(items)

    def choose_stereotype(self, items: List[StereotypeItem], buffers: AgentBuffers, new_item: StereotypeItem) -> Optional[StereotypeItem]:
        if not items:
            return None

        # First try and evict items whcih we do not have other information for
        aware_crypto = {
            item.agent: buffers.find_crypto(item.agent)
            for item in items
        }
        #aware_trust = {
        #    (item.agent, item.capability): buffers.find_trust(item.agent, item.capability)
        #    item for item in items
        #}
        #aware_reputation = {
        #    item.agent: buffers.find_reputation(item.agent)
        #    item for item in items
        #}

        chosen = [
            item
            for item in items
            if aware_crypto[item.agent] is None
            #and aware_trust[(item.agent, item.capability)] is None
            #and aware_reputation[item.agent] is None
        ]
        if chosen:
            return self._lru(chosen)

        return self._lru(items)

    def use_common(self, item: List):
        if item is None:
            return

        item.eviction_data = self.sim.current_time
"""
