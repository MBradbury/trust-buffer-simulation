from __future__ import annotations

from enum import Enum

from hmmlearn.hmm import MultinomialHMM
import numpy as np

class CapabilityBehaviourState(Enum):
    WellBehaved = 1
    BadlyBehaved = 2

class InteractionObservation(Enum):
    Correct = 1
    Incorrect = 2

class CapabilityBehaviour:
    def __init__(self):
        self.states = list(CapabilityBehaviourState)
        self.observations = list(InteractionObservation)

        self.hmm = MultinomialHMM(n_components=len(self.states))

        self.state_history: list[tuple[float, CapabilityBehaviourState]] = []

        # When many similar capabilities are being used, it is quite often
        # the case that they will be in the same state. This means agent
        # capabilities will have the same results as each other.
        # This can lead to bad cases, for example, where VeryGood behaviours
        # all fail at the same time.
        # To prevent this synchronisation, each behaviour is given their own
        # different initial seed to mix with the seed provided for an interaction.
        self.individual_seed: int = 0

    def next_interaction(self, seed: int, t: float) -> InteractionObservation:
        (x, state_sequence) = self.hmm.sample(1, random_state=seed ^ self.individual_seed)

        assert len(state_sequence) == 1
        assert len(x) == 1
        assert len(x[0]) == 1

        chosen_state = np.array([
            1 if state_sequence[0] == n else 0
            for n in range(len(self.states))
        ])

        # Update the state of where the HMM is
        self.hmm.startprob_ = chosen_state @ self.hmm.transmat_

        self.state_history.append((t, self.states[state_sequence[0]]))

        return self.observations[x[0][0]]

    def peek_interaction(self, seed: int) -> InteractionObservation:
        (x, state_sequence) = self.hmm.sample(1, random_state=seed ^ self.individual_seed)

        assert len(state_sequence) == 1
        assert len(x) == 1
        assert len(x[0]) == 1

        return self.observations[x[0][0]]

    @property
    def brs_stereotype(self) -> tuple[int, int]:
        raise NotImplementedError()

"""
Numpy is row-major

The start probability is: pi : CapabilityBehaviourState -> [0,1]
[WellBehaved, BadlyBehaved]

The transition behaviour is: A : CapabilityBehaviourState x CapabilityBehaviourState -> [0,1]
[
    [WellBehaved->WellBehaved,  WellBehaved->BadlyBehaved ],
    [BadlyBehaved->WellBehaved, BadlyBehaved->BadlyBehaved],
]

The observation behaviour is: A : CapabilityBehaviourState x InteractionObservation -> [0,1]
[
    [WellBehaved->Correct,  WellBehaved->Incorrect ],
    [BadlyBehaved->Correct, BadlyBehaved->Incorrect],
]
"""

class AlwaysGoodBehaviour(CapabilityBehaviour):
    def __init__(self):
        super().__init__()

        self.hmm.startprob_ = np.array([1, 0])

        self.hmm.transmat_ = np.array([
            [1, 0],
            [0, 1]
        ])

        self.hmm.emissionprob_ = np.array([
            [1, 0],
            [0, 1]
        ])

    def next_interaction(self, seed: int, t: float) -> InteractionObservation:
        result = super().next_interaction(seed, t)
        assert result is InteractionObservation.Correct
        return result

    def peek_interaction(self, seed: int) -> InteractionObservation:
        result = super().peek_interaction(seed)
        assert result is InteractionObservation.Correct
        return result

    @property
    def brs_stereotype(self) -> tuple[int, int]:
        return (20, 0)

class AlwaysBadBehaviour(CapabilityBehaviour):
    def __init__(self):
        super().__init__()

        self.hmm.startprob_ = np.array([0, 1])

        self.hmm.transmat_ = np.array([
            [1, 0],
            [0, 1]
        ])

        self.hmm.emissionprob_ = np.array([
            [1, 0],
            [0, 1]
        ])

    def next_interaction(self, seed: int, t: float) -> InteractionObservation:
        result = super().next_interaction(seed, t)
        assert result is InteractionObservation.Incorrect
        return result

    def peek_interaction(self, seed: int) -> InteractionObservation:
        result = super().peek_interaction(seed)
        assert result is InteractionObservation.Incorrect
        return result

    @property
    def brs_stereotype(self) -> tuple[int, int]:
        return (0, 20)

class VeryGoodBehaviour(CapabilityBehaviour):
    def __init__(self):
        super().__init__()

        self.hmm.startprob_ = np.array([0.99, 0.01])

        self.hmm.transmat_ = np.array([
            [0.99, 0.01],
            [0.80, 0.20]
        ])

        self.hmm.emissionprob_ = np.array([
            [0.99, 0.01],
            [0, 1]
        ])

    @property
    def brs_stereotype(self) -> tuple[int, int]:
        return (19, 1)

class GoodBehaviour(CapabilityBehaviour):
    def __init__(self):
        super().__init__()

        self.hmm.startprob_ = np.array([0.9, 0.1])

        self.hmm.transmat_ = np.array([
            [0.9, 0.1],
            [0.6, 0.4]
        ])

        self.hmm.emissionprob_ = np.array([
            [0.9, 0.1],
            [0, 1]
        ])

    @property
    def brs_stereotype(self) -> tuple[int, int]:
        return (15, 5)

class UnstableBehaviour(CapabilityBehaviour):
    def __init__(self):
        super().__init__()

        self.hmm.startprob_ = np.array([0.5, 0.5])

        self.hmm.transmat_ = np.array([
            [0.5, 0.5],
            [0.5, 0.5]
        ])

        self.hmm.emissionprob_ = np.array([
            [0.9, 0.1],
            [0, 1]
        ])

    @property
    def brs_stereotype(self) -> tuple[int, int]:
        return (10, 10)
