
from frozenlist import FrozenList

# from: https://stackoverflow.com/questions/17526659/how-to-set-a-max-length-for-a-python-list-set

class BoundExceedError(RuntimeError):
    pass

class BoundedList(FrozenList):
    def __init__(self, *args, **kwargs):
        self.length = kwargs.pop('length', None)
        super().__init__(*args, **kwargs)

    def _check_item_bound(self):
        if self.length and len(self) >= self.length:
            raise BoundExceedError()

    def _check_list_bound(self, L):
        if self.length and len(self) + len(L) > self.length:
            raise BoundExceedError()

    def append(self, x):
        self._check_item_bound()
        return super().append(x)

    def extend(self, L):
        self._check_list_bound(L)
        return super().extend(L)

    def insert(self, i, x):
        self._check_item_bound()
        return super().insert(i, x)

    def __add__(self, L):
        self._check_list_bound(L)
        return super().__add__(L)

    def __iadd__(self, L):
        self._check_list_bound(L)
        return super().__iadd__(L)

    def __setslice__(self, *args, **kwargs):
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
