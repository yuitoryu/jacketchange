from pathlib import Path
from beartype import beartype

class Jacket:
    @beartype
    def __init__(self, id: int, cur_id: int):
        self.id = id
        self.cur_id = cur_id
        
    def set_id(self, new_id: int) -> None:
        self.id = new_id
        
    def get_id(self) -> int:
        return self.id

    def __repr__(self) -> str:
        return str((['id', self.id], ['use_pic', self.cur_id]))

class DiffManager:
    @beartype
    def __init__(self, id: str, jacket_t_loc: dict[str, str], diff_list: list[int]):
        # self.jacket_t_loc = sorted({int(k): v for k, v in jacket_t_loc.items()})
        self.jackets = sorted(int(k) for k in jacket_t_loc.keys())
        self.diffs = {diff:i for i, diff in enumerate(diff_list)}
        
        # 填充曲绘文件使用情况
        self.jacket_usage: list[None | Jacket]= [None] * len(self.diffs)
        for i, diff in enumerate(self.jackets):
            cur = Jacket(diff, diff)
            for j in range(self.diffs[diff], len(self.jacket_usage)):
                self.jacket_usage[j] = cur

        
    def __repr__(self) -> str:
        return '\n'.join([ jacket.__repr__() for jacket in self.jacket_usage])
        
            
            