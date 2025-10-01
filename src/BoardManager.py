"""
BoardManager.py
Description: Manages the game board state for Minesweeper. Owns the Cell class representing
each cell and the BoardManager class for the grid.
Inputs: None
Outputs: None
Author: Landon Bever
Editor: Asa Maker
External Sources Used: None, all code is original
Creation Date: 09/10/2024
"""

import random
from typing import List, Tuple, Optional


class Cell:
    """Represents a single cell on the Minesweeper board."""

    def __init__(self) -> None:
        """Initialize cell properties."""
        self.is_covered: bool = True
        self.flagged: bool = False
        self.is_mine: bool = False
        self.neighbor_count: int = 0

    def reset(self) -> None:
        """Reset cell to initial state."""
        self.is_covered = True
        self.flagged = False
        self.is_mine = False
        self.neighbor_count = 0


class BoardManager:
    """Manages the Minesweeper board."""

    def __init__(self, rows: int = 10, cols: int = 10) -> None:
        """Initialize board with given dimensions."""
        self.rows = rows
        self.cols = cols
        self.grid: List[List[Cell]] = [[Cell() for _ in range(cols)] for _ in range(rows)]

    def in_bounds(self, r: int, c: int) -> bool:
        """Check if (r, c) is within board."""
        return 0 <= r < self.rows and 0 <= c < self.cols

    def neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Return a list of in-bounds neighbor coordinates around (r, c)."""
        result: List[Tuple[int, int]] = []
        for nr in range(r - 1, r + 2):
            for nc in range(c - 1, c + 2):
                if (nr, nc) == (r, c):
                    continue
                if self.in_bounds(nr, nc):
                    result.append((nr, nc))
        return result

    def reset(self) -> None:
        """Reset all cells."""
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid[r][c].reset()

    def clear_mines_and_counts(self) -> None:
        """Remove all mines and set neighbor counts to 0."""
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                cell.is_mine = False
                cell.neighbor_count = 0

    def adjust_neighbor_counts(self, r: int, c: int, amount: int) -> None:
        """Adjust neighbor_count in 3x3 area around (r, c) by `amount`."""
        for nr in range(r - 1, r + 2):
            for nc in range(c - 1, c + 2):
                if self.in_bounds(nr, nc):
                    self.grid[nr][nc].neighbor_count += amount

    def set_mine(self, r: int, c: int, value: bool) -> None:
        """Mine setter with neighbor count updates."""
        cell = self.grid[r][c]
        if cell.is_mine == value:
            return
        cell.is_mine = value
        if value:
            # If placing a mine, increment neighbor counts around it
            self.adjust_neighbor_counts(r, c, 1)
        else:
            # If removing a mine, decrement neighbor counts around it
            self.adjust_neighbor_counts(r, c, -1)

    def toggle_mine(self, r: int, c: int) -> None:
        """Toggle mine at (r, c)."""
        self.set_mine(r, c, not self.grid[r][c].is_mine)

    def place_unique_mines(self, total_mines: int, exclude: Optional[Tuple[int, int]] = None) -> None:
        """Place mines at unique random locations; guarantee (exclude) safe if provided."""
        self.clear_mines_and_counts()
        coords: List[Tuple[int, int]] = []

        for r in range(self.rows):
            for c in range(self.cols):
                if exclude is None or (r, c) != exclude:
                    coords.append((r, c))

        chosen = random.sample(coords, k=total_mines)
        for rr, cc in chosen:
            self.set_mine(rr, cc, True)

    def uncover(self, r: int, c: int) -> None:
        """Uncover cell at (r, c)."""
        self.grid[r][c].is_covered = False

    def cover(self, r: int, c: int) -> None:
        """Cover cell at (r, c)."""
        self.grid[r][c].is_covered = True

    def set_flag(self, r: int, c: int, value: bool) -> None:
        """Set flag state at (r, c)."""
        self.grid[r][c].flagged = value

    def toggle_flag(self, r: int, c: int) -> None:
        """Toggle flag state at (r, c)."""
        self.grid[r][c].flagged = not self.grid[r][c].flagged

    def cell(self, r: int, c: int) -> Cell:
        """Get cell at (r, c)."""
        return self.grid[r][c]
