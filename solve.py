from __future__ import annotations

import argparse
import os
from typing import List

from wordhunt.solver import SolveConfig, solve_grid, solve_grid_with_paths
from wordhunt.trie import Trie


def load_words(path: str, min_len: int) -> List[str]:
    words: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            w = line.strip().lower()
            if len(w) >= min_len and w.isalpha():
                words.append(w)
    return words


def parse_grid(grid_str: str, size: int) -> List[List[str]]:
    """
    Accepts grid input in these forms:
      1) Multiline rows (best):  RNSM\nTDUO\nRASA\nETHH
      2) Slash rows:             r n s m / t d u o / r a s a / e t h h
      3) Compact string:         RNSMTDUORASAETHH
      4) Spaced multiline:       r n s m\n t d u o\n r a s a\n e t h h
    """
    s = grid_str.strip().lower()

    # Case 1 or 4: multiline input (preferred)
    if "\n" in s:
        lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
        if len(lines) != size:
            raise ValueError(f"Expected {size} rows, got {len(lines)}.")

        grid: List[List[str]] = []
        for ln in lines:
            # if the line has spaces, treat it as tokens; otherwise treat as characters
            if " " in ln:
                row = [tok for tok in ln.split() if tok]
            else:
                row = [ch for ch in ln if ch.isalpha()]
            if len(row) != size:
                raise ValueError(f"Each row must have {size} letters. Got: {ln!r}")
            grid.append(row)
        return grid

    # Case 2: slash-separated rows
    if "/" in s:
        rows = [row.strip() for row in s.split("/")]
        grid = []
        for row in rows:
            parts = [p for p in row.split() if p]
            if len(parts) == size:
                grid.append(parts)
            else:
                letters = [ch for ch in row if ch.isalpha()]
                if len(letters) != size:
                    raise ValueError(f"Expected {size} letters per row in slash format. Got: {row!r}")
                grid.append(letters)

        if len(grid) != size:
            raise ValueError(f"Expected {size} rows in slash format, got {len(grid)}.")
        return grid

    # Case 3: compact input (letters only)
    compact = "".join(ch for ch in s if ch.isalpha())
    if len(compact) != size * size:
        raise ValueError(f"Expected {size*size} letters, got {len(compact)}.")
    it = iter(compact)
    return [[next(it) for _ in range(size)] for _ in range(size)]

def wordhunt_score(word: str) -> int:
    # Common Boggle/Word Hunt scoring
    n = len(word)
    if n < 3:
        return 0
    if n <= 4:
        return 1
    if n == 5:
        return 2
    if n == 6:
        return 3
    if n == 7:
        return 5
    return 11  # 8+

def main() -> None:
    ap = argparse.ArgumentParser(description="Word Hunt / Boggle-style solver (8-direction adjacency).")
    ap.add_argument("--grid", help='Grid input (supports multiline, slashes, or compact).')
    ap.add_argument("--grid-file", help="Path to a text file containing the grid (e.g. 4 lines for 4x4).")
    ap.add_argument("--size", type=int, default=4, help="Grid size N for NxN. Default 4.")
    ap.add_argument("--dict", dest="dict_path", default="wordlists/words.txt", help="Path to word list file.")
    ap.add_argument("--min-len", type=int, default=3, help="Minimum word length. Default 3.")
    ap.add_argument("--no-diagonal", action="store_true", help="Disable diagonal adjacency.")
    ap.add_argument("--top", type=int, default=0, help="Show only top N words (sorted by length desc). 0 = all.")
    ap.add_argument("--min-score", type=int, default=0, help="Minimum Word Hunt score to include.")
    ap.add_argument("--paths", action="store_true", help="Show one coordinate path for each word.")
    args = ap.parse_args()

    if not os.path.exists(args.dict_path):
        raise SystemExit(
            f"Dictionary file not found: {args.dict_path}\n"
            f"Add one at that path, or pass --dict /path/to/wordlist.txt"
        )

    if not args.grid and not args.grid_file:
        raise SystemExit("Provide either --grid or --grid-file")

    if args.grid_file:
        with open(args.grid_file, "r", encoding="utf-8") as f:
            grid_input = f.read()
    else:
        grid_input = args.grid

    grid = parse_grid(grid_input, args.size)
    print("\nBoard:")
    for r, row in enumerate(grid, start=1):
        print(f"{r}: " + " ".join(ch.upper() for ch in row))
    print("    " + " ".join(str(c) for c in range(1, len(grid[0]) + 1)))
    print()

    words = load_words(args.dict_path, args.min_len)
    trie = Trie()
    for w in words:
        trie.insert(w)

    cfg = SolveConfig(
        min_len=args.min_len,
        allow_diagonal=not args.no_diagonal,
    )

    if args.paths:
        found_paths = solve_grid_with_paths(grid, trie, cfg)
        found_words = set(found_paths.keys())
    else:
        found_words = solve_grid(grid, trie, cfg)

    sorted_words = sorted(found_words, key=lambda w: (-wordhunt_score(w), -len(w), w))

    if args.min_score > 0:
        sorted_words = [w for w in sorted_words if wordhunt_score(w) >= args.min_score]

    if args.top and args.top > 0:
        sorted_words = sorted_words[: args.top]

    for w in sorted_words:
        if args.paths:
            path = found_paths[w]
            path_str = "->".join(f"({r+1},{c+1})" for r, c in path)
            print(f"{wordhunt_score(w):>2}  {w} ({len(w)})  {path_str}")
        else:
            print(f"{wordhunt_score(w):>2}  {w} ({len(w)})")

    print(f"\nFound {len(found_words)} words (min_len={args.min_len}, size={args.size}).")


if __name__ == "__main__":
    main()
