from __future__ import annotations

from typing import Optional, TypeVar, Sequence

import numpy as np

from typing import TYPE_CHECKING

from simulation.agent_buffers import AgentBuffers, ChallengeResponseItem
if TYPE_CHECKING:
    from simulation.simulator import Simulator
    from simulation.agent_buffers import AgentBuffers, CryptoItem, TrustItem, ReputationItem, StereotypeItem, ChallengeResponseItem

    ItemT = TypeVar('ItemT', CryptoItem, TrustItem, ReputationItem, StereotypeItem, ChallengeResponseItem)

class EvictionStrategy:
    short_name = "Base"

    def __init__(self, sim: Simulator):
        self.sim = sim

    def add_common(self, item: ItemT):
        pass

    def add_crypto(self, item: CryptoItem):
        return self.add_common(item)
    def add_trust(self, item: TrustItem):
        return self.add_common(item)
    def add_reputation(self, item: ReputationItem):
        return self.add_common(item)
    def add_stereotype(self, item: StereotypeItem):
        return self.add_common(item)
    def add_challenge_response(self, item: ChallengeResponseItem):
        return self.add_common(item)

    def choose_common(self, items: Sequence[ItemT], buffers: AgentBuffers, new_item: ItemT) -> Optional[ItemT]:
        raise NotImplementedError()

    def choose_crypto(self, items: Sequence[CryptoItem], buffers: AgentBuffers, new_item: CryptoItem) -> Optional[CryptoItem]:
        return self.choose_common(items, buffers, new_item)
    def choose_trust(self, items: Sequence[TrustItem], buffers: AgentBuffers, new_item: TrustItem) -> Optional[TrustItem]:
        return self.choose_common(items, buffers, new_item)
    def choose_reputation(self, items: Sequence[ReputationItem], buffers: AgentBuffers, new_item: ReputationItem) -> Optional[ReputationItem]:
        return self.choose_common(items, buffers, new_item)
    def choose_stereotype(self, items: Sequence[StereotypeItem], buffers: AgentBuffers, new_item: StereotypeItem) -> Optional[StereotypeItem]:
        return self.choose_common(items, buffers, new_item)
    def choose_challenge_response(self, items: Sequence[ChallengeResponseItem], buffers: AgentBuffers, new_item: ChallengeResponseItem) -> Optional[ChallengeResponseItem]:
        return self.choose_common(items, buffers, new_item)

    def use_common(self, item: ItemT | None):
        pass

    def use_crypto(self, item: CryptoItem | None):
        return self.use_common(item)
    def use_trust(self, item: TrustItem | None):
        return self.use_common(item)
    def use_reputation(self, item: ReputationItem | None):
        return self.use_common(item)
    def use_stereotype(self, item: StereotypeItem | None):
        return self.use_common(item)
    def use_challenge_response(self, item: ChallengeResponseItem | None):
        return self.use_common(item)

class NoneEvictionStrategy(EvictionStrategy):
    short_name = "None"

    def choose_common(self, items: Sequence[ItemT], buffers: AgentBuffers, new_item: ItemT) -> Optional[ItemT]:
        return None

class RandomEvictionStrategy(EvictionStrategy):
    short_name = "Random"

    def choose_common(self, items: Sequence[ItemT], buffers: AgentBuffers, new_item: ItemT) -> Optional[ItemT]:
        return self.sim.rng.choice(items)

class FIFOEvictionStrategy(EvictionStrategy):
    short_name = "FIFO"

    def add_common(self, item: ItemT):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: Sequence[ItemT], buffers: AgentBuffers, new_item: ItemT) -> Optional[ItemT]:
        return min(items, key=lambda x: x.eviction_data)

class LRUEvictionStrategy(EvictionStrategy):
    short_name = "LRU"

    def add_common(self, item: ItemT):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: Sequence[ItemT], buffers: AgentBuffers, new_item: ItemT) -> Optional[ItemT]:
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: ItemT | None):
        if item is None:
            return

        item.eviction_data = self.sim.current_time

class LRU2EvictionStrategy(EvictionStrategy):
    short_name = "LRU2"

    def add_common(self, item: ItemT):
        item.eviction_data = (self.sim.current_time, self.sim.current_time)

    def choose_common(self, items: Sequence[ItemT], buffers: AgentBuffers, new_item: ItemT) -> Optional[ItemT]:
        return min(items, key=lambda x: x.eviction_data[1])

    def use_common(self, item: ItemT | None):
        if item is None:
            return

        item.eviction_data = (self.sim.current_time, item.eviction_data[0])

class MRUEvictionStrategy(EvictionStrategy):
    short_name = "MRU"

    def add_common(self, item: ItemT):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: Sequence[ItemT], buffers: AgentBuffers, new_item: ItemT) -> Optional[ItemT]:
        return max(items, key=lambda x: x.eviction_data)

    def use_common(self, item: ItemT | None):
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

    def add_common(self, item: ItemT):
        item.eviction_data = self.sim.current_time

    def choose_trust(self, items: Sequence[TrustItem], buffers: AgentBuffers, new_item: TrustItem) -> Optional[TrustItem]:
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

    def choose_common(self, items: Sequence[ItemT], buffers: AgentBuffers, new_item: ItemT) -> Optional[ItemT]:
        # Do LRU for everything else
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: ItemT | None):
        if item is None:
            return

        item.eviction_data = self.sim.current_time

class FiveBandEvictionStrategy(EvictionStrategy):
    short_name = "FiveBand"

    def add_common(self, item: ItemT):
        item.eviction_data = self.sim.current_time

    def choose_trust(self, items: Sequence[TrustItem], buffers: AgentBuffers, new_item: TrustItem) -> Optional[TrustItem]:
        item_trust = [item.brs_trust() for item in items]

        quantile = np.quantile(item_trust, [0.2, 0.4, 0.6, 0.8, 1.0])

        # Keep the 20% best and worst nodes as they provide useful information
        # Keep the middle 20% nodes as they may not have had a chance to stabilise
        # Consider removing the inbetween nodes that are neither very good or very bad

        low, lowmid, mid, highmid, _high = quantile

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

    def choose_common(self, items: Sequence[ItemT], buffers: AgentBuffers, new_item: ItemT) -> Optional[ItemT]:
        # Do LRU for everything else
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: ItemT | None):
        if item is None:
            return

        item.eviction_data = self.sim.current_time


class NotInOtherEvictionStrategy(EvictionStrategy):
    short_name = "NotInOther"

    def add_common(self, item: ItemT):
        item.eviction_data = self.sim.current_time

    def _lru(self, choices: Sequence[tuple[ItemT, int]]) -> ItemT | None:
        if not choices:
            return None

        selected = [item for (item, count) in choices if count == 0]

        if selected:
            return min(selected, key=lambda x: x.eviction_data)
        else:
            selected = [item for (item, _count) in choices]
            return min(selected, key=lambda x: x.eviction_data)

    def choose_crypto(self, items: Sequence[CryptoItem], buffers: AgentBuffers, new_item: CryptoItem) -> Optional[CryptoItem]:
        choices = [
            (item, buffers.buffer_has_agent_count(item.agent, "TRS"))
            for item in items
        ]
        return self._lru(choices)

    def choose_trust(self, items: Sequence[TrustItem], buffers: AgentBuffers, new_item: TrustItem) -> Optional[TrustItem]:
        choices = [
            (item, buffers.buffer_has_agent_capability_count(item.agent, item.capability, "CRS"))
            for item in items
        ]
        return self._lru(choices)

    def choose_reputation(self, items: Sequence[ReputationItem], buffers: AgentBuffers, new_item: ReputationItem) -> Optional[ReputationItem]:
        choices = [
            (item, sum(buffers.buffer_has_agent_capability_count(trust_item.agent, trust_item.capability, "CTS") for trust_item in item.trust_items))
            for item in items
        ]
        return self._lru(choices)

    def choose_stereotype(self, items: Sequence[StereotypeItem], buffers: AgentBuffers, new_item: StereotypeItem) -> Optional[StereotypeItem]:
        choices = [
            (item, buffers.buffer_has_agent_capability_count(item.agent, item.capability, "CTR"))
            for item in items
        ]
        return self._lru(choices)

    def choose_challenge_response(self, items: Sequence[ChallengeResponseItem], buffers: AgentBuffers, new_item: ChallengeResponseItem) -> ChallengeResponseItem | None:
        # Do LRU
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: ItemT | None):
        if item is None:
            return

        item.eviction_data = self.sim.current_time


class MinNotInOtherEvictionStrategy(EvictionStrategy):
    short_name = "MinNotInOther"

    def add_common(self, item: ItemT):
        item.eviction_data = self.sim.current_time

    def _lru(self, choices: Sequence[tuple[ItemT, int]]) -> ItemT | None:
        if not choices:
            return None

        min_count = min(choices, key=lambda x: x[1])[1]

        selected = [item for (item, count) in choices if count == min_count]

        return min(selected, key=lambda x: x.eviction_data)

    def choose_crypto(self, items: Sequence[CryptoItem], buffers: AgentBuffers, new_item: CryptoItem) -> Optional[CryptoItem]:
        choices = [
            (item, buffers.buffer_has_agent_count(item.agent, "TRS"))
            for item in items
        ]
        return self._lru(choices)

    def choose_trust(self, items: Sequence[TrustItem], buffers: AgentBuffers, new_item: TrustItem) -> Optional[TrustItem]:
        choices = [
            (item, buffers.buffer_has_agent_capability_count(item.agent, item.capability, "CRS"))
            for item in items
        ]
        return self._lru(choices)

    def choose_reputation(self, items: Sequence[ReputationItem], buffers: AgentBuffers, new_item: ReputationItem) -> Optional[ReputationItem]:
        choices = [
            (item, sum(buffers.buffer_has_agent_capability_count(trust_item.agent, trust_item.capability, "CTS") for trust_item in item.trust_items))
            for item in items
        ]
        return self._lru(choices)

    def choose_stereotype(self, items: Sequence[StereotypeItem], buffers: AgentBuffers, new_item: StereotypeItem) -> Optional[StereotypeItem]:
        choices = [
            (item, buffers.buffer_has_agent_capability_count(item.agent, item.capability, "CTR"))
            for item in items
        ]
        return self._lru(choices)

    def choose_challenge_response(self, items: Sequence[ChallengeResponseItem], buffers: AgentBuffers, new_item: ChallengeResponseItem) -> ChallengeResponseItem | None:
        # Do LRU
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: ItemT | None):
        if item is None:
            return

        item.eviction_data = self.sim.current_time


class CapabilityPriorityEvictionStrategy(EvictionStrategy):
    short_name = "CapPri"

    def add_common(self, item: ItemT):
        item.eviction_data = self.sim.current_time

    def _lru(self, choices: Sequence[tuple[ItemT, int]]) -> ItemT | None:
        if not choices:
            return None

        min_priority = min(choices, key=lambda x: x[1])[1]

        selected = [item for (item, priority) in choices if priority == min_priority]

        return min(selected, key=lambda x: x.eviction_data)

    def choose_crypto(self, items: Sequence[CryptoItem], buffers: AgentBuffers, new_item: CryptoItem) -> Optional[CryptoItem]:
        return self._lru([(item, max(capability.priority for capability in item.agent.capabilities)) for item in items])

    def choose_trust(self, items: Sequence[TrustItem], buffers: AgentBuffers, new_item: TrustItem) -> Optional[TrustItem]:
        return self._lru([(item, item.capability.priority) for item in items])

    def choose_reputation(self, items: Sequence[ReputationItem], buffers: AgentBuffers, new_item: ReputationItem) -> Optional[ReputationItem]:
        return self._lru([(item, max(trust_item.capability.priority for trust_item in item.trust_items) if item.trust_items else -1) for item in items])

    def choose_stereotype(self, items: Sequence[StereotypeItem], buffers: AgentBuffers, new_item: StereotypeItem) -> Optional[StereotypeItem]:
        return self._lru([(item, item.capability.priority) for item in items])

    def choose_challenge_response(self, items: Sequence[ChallengeResponseItem], buffers: AgentBuffers, new_item: ChallengeResponseItem) -> ChallengeResponseItem | None:
        # Do LRU
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: ItemT | None):
        if item is None:
            return

        item.eviction_data = self.sim.current_time

class CuckooEvictionStrategy(EvictionStrategy):
    """
    Prefers to evict items about agents that are in the badlist first.
    If none in the badlist, then falls back to LRU.
    """
    short_name = "Cuckoo"

    def add_common(self, item: ItemT):
        item.eviction_data = self.sim.current_time

    def choose_common(self, items: Sequence[ItemT], buffers: AgentBuffers, new_item: ItemT) -> Optional[ItemT]:
        assert buffers.badlist is not None

        # No items to choose from to evict
        if not items:
            return None

        # Evict badlisted agents first
        badlisted_items = [item for item in items if buffers.badlist.contains(item.agent.eui64)]
        if badlisted_items:
            # Do LRU on badlisted items
            return min(items, key=lambda x: x.eviction_data)

        # Otherwise do LRU
        return min(items, key=lambda x: x.eviction_data)

    def use_common(self, item: ItemT | None):
        if item is None:
            return

        item.eviction_data = self.sim.current_time
