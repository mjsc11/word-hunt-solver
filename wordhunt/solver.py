from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set, Tuple

from .trie import Trie


Coord = Tuple[int, int]


@dataclass(frozen=True)
class SolveConfig:
    min_len: int = 3
    allow_diagonal: bool = True


def _neighbors(r: int, c: int, rows: int, cols: int, allow_diagonal: bool) -> Iterable[Coord]:
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if allow_diagonal:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dr, dc in deltas:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            yield nr, nc


def solve_grid(grid: List[List[str]], trie: Trie, cfg: SolveConfig) -> Set[str]:
    if not grid or not grid[0]:
        return set()

    rows, cols = len(grid), len(grid[0])
    out: Set[str] = set()
    visited = [[False] * cols for _ in range(rows)]

    g = [[cell.lower().strip() for cell in row] for row in grid]

    def dfs(r: int, c: int, current: str) -> None:
        visited[r][c] = True

        token = g[r][c]
        next_word = current + token

        if not trie.has_prefix(next_word):
            visited[r][c] = False
            return

        if len(next_word) >= cfg.min_len and trie.has_word(next_word):
            out.add(next_word)

        for nr, nc in _neighbors(r, c, rows, cols, cfg.allow_diagonal):
            if not visited[nr][nc]:
                dfs(nr, nc, next_word)

        visited[r][c] = False

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, "")

    return out

def solve_grid_with_paths(grid: List[List[str]], trie: Trie, cfg: SolveConfig) -> dict[str, list[Coord]]:
    """
    Returns one path per found word: {word: [(r,c), (r,c), ...]}
    Coordinates are 0-based (top-left is (0,0)).
    """
    if not grid or not grid[0]:
        return {}

    rows, cols = len(grid), len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    g = [[cell.lower().strip() for cell in row] for row in grid]

    paths: dict[str, list[Coord]] = {}

    def dfs(r: int, c: int, current: str, path: list[Coord]) -> None:
        visited[r][c] = True

        token = g[r][c]
        next_word = current + token
        path.append((r, c))

        # prefix prune
        if not trie.has_prefix(next_word):
            path.pop()
            visited[r][c] = False
            return

        if len(next_word) >= cfg.min_len and trie.has_word(next_word):
            # store the first path we find for this word
            if next_word not in paths:
                paths[next_word] = path.copy()

        for nr, nc in _neighbors(r, c, rows, cols, cfg.allow_diagonal):
            if not visited[nr][nc]:
                dfs(nr, nc, next_word, path)

        path.pop()
        visited[r][c] = False

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, "", [])

    return paths
