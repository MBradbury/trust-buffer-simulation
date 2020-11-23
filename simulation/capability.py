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

        self.state_history = []

    def next_interaction(self, seed: int, t: float):
        (x, state_sequence) = self.hmm.sample(1, random_state=seed)

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

    def peek_interaction(self, seed: int):
        (x, state_sequence) = self.hmm.sample(1, random_state=seed)

        assert len(state_sequence) == 1
        assert len(x) == 1
        assert len(x[0]) == 1

        return self.observations[x[0][0]]

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
    brs_stereotype = (20, 0)

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

class AlwaysBadBehaviour(CapabilityBehaviour):
    brs_stereotype = (0, 20)

    def __init__(self):
        super().__init__()

        self.hmm.startprob_ = np.array([0, 1])

        self.hmm.transmat_ = np.array([
            [0, 1],
            [1, 0]
        ])

        self.hmm.emissionprob_ = np.array([
            [1, 0],
            [0, 1]
        ])

class VeryGoodBehaviour(CapabilityBehaviour):
    brs_stereotype = (19, 1)

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

class GoodBehaviour(CapabilityBehaviour):
    brs_stereotype = (15, 5)

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

class UnstableBehaviour(CapabilityBehaviour):
    brs_stereotype = (10, 10)

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

# TODO: may transfer into always good/always bad
#class EventuallyStableBehaviour(CapabilityBehaviour):
#    pass

class Capability:
    def __init__(self, name: str, task_period: float):
        self.name = name
        self.task_period = task_period

    def next_task_period(self, rng: random.Random) -> float:
        return rng.expovariate(1.0 / self.task_period)

    def __repr__(self):
        return f"Capability({self.name})"

    def __str__(self):
        return self.name
