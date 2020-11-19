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

        # Update the state of where the HMM is
        self.hmm.startprob_ = np.array([
            1 if state_sequence[0] == n else 0
            for n in range(len(self.states))
        ])

        self.state_history.append((t, self.states[state_sequence[0]]))

        return self.observations[x[0][0]]

    def peek_interaction(self, seed):
        (x, state_sequence) = self.hmm.sample(1, random_state=seed)

        assert len(state_sequence) == 1
        assert len(x) == 1
        assert len(x[0]) == 1

        return self.observations[x[0][0]]



class AlwaysGoodBehaviour(CapabilityBehaviour):
    def __init__(self):
        super().__init__()

        self.hmm.startprob_ = np.array([1, 0])

        self.hmm.transmat_ = np.array([[1, 0], [0, 1]])

        self.hmm.emissionprob_ = np.array([[1, 0], [0, 1]])

class AlwaysBadBehaviour(CapabilityBehaviour):
    def __init__(self):
        super().__init__()

        self.hmm.startprob_ = np.array([0, 1])

        self.hmm.transmat_ = np.array([[0, 1], [1, 0]])

        self.hmm.emissionprob_ = np.array([[0, 1], [1, 0]])

class VeryGoodBehaviour(CapabilityBehaviour):
    def __init__(self):
        super().__init__()

        self.hmm.startprob_ = np.array([0.99, 0.01])

        self.hmm.transmat_ = np.array([[0.99, 0.01], [0.01, 0.99]])

        self.hmm.emissionprob_ = np.array([[0.99, 0.01], [0, 1]])

class GoodBehaviour(CapabilityBehaviour):
    def __init__(self):
        super().__init__()

        self.hmm.startprob_ = np.array([0.9, 0.1])

        self.hmm.transmat_ = np.array([[0.9, 0.1], [0.1, 0.9]])

        self.hmm.emissionprob_ = np.array([[0.9, 0.1], [0, 1]])

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
