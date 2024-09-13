from typing import TypeVar, Any, Sequence
from typing_extensions import Self

from frozenlist import FrozenList

# from: https://stackoverflow.com/questions/17526659/how-to-set-a-max-length-for-a-python-list-set

T = TypeVar('T')

class BoundExceedError(RuntimeError):
    pass

class BoundedList(FrozenList[T]):
    def __init__(self, *args: Any, length: int, **kwargs: Any):
        self.length = length
        super().__init__(*args, **kwargs)

    def _check_item_bound(self):
        if self.length and len(self) >= self.length:
            raise BoundExceedError()

    def _check_list_bound(self, values: Sequence[T]):
        if self.length and len(self) + len(values) > self.length:
            raise BoundExceedError()

    def append(self, value: T):
        self._check_item_bound()
        return super().append(value)

    def extend(self, values: Sequence[T]) -> None: # type: ignore
        self._check_list_bound(values)
        return super().extend(values)

    def insert(self, pos: int, item: T):
        self._check_item_bound()
        return super().insert(pos, item)

    def __iadd__(self, values: Sequence[T]) -> Self: # type: ignore
        self._check_list_bound(values)
        return super().__iadd__(values)
