from typing import TypeVar, Any, Sequence

from frozenlist import FrozenList

# from: https://stackoverflow.com/questions/17526659/how-to-set-a-max-length-for-a-python-list-set

T = TypeVar('T')

class BoundExceedError(RuntimeError):
    pass

class BoundedList(FrozenList[T]):
    def __init__(self, *args: Any, **kwargs: Any):
        self.length = kwargs.pop('length', None)
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

    def extend(self, values: Sequence[T]) -> None:
        self._check_list_bound(values)
        return super().extend(values)

    def insert(self, pos: int, item: T):
        self._check_item_bound()
        return super().insert(pos, item)

    def __add__(self, values: Sequence[T]) -> FrozenList[T]:
        self._check_list_bound(values)
        return super().__add__(values)

    def __iadd__(self, values: Sequence[T]) -> None:
        self._check_list_bound(values)
        return super().__iadd__(values)

    def __setslice__(self, *args: Any, **kwargs: Any) -> None:
        if len(args) > 2 and self.length:
            left, right, L = args[0], args[1], args[2]
            if right > self.length:
                if left + len(L) > self.length:
                    raise BoundExceedError()
            else:
                len_del = (right - left)
                len_add = len(L)
                if len(self) - len_del + len_add > self.length:
                    raise BoundExceedError()
        return super().__setslice__(*args, **kwargs)
