"""
Module: AISolver
Description: Implements AI solver with three difficulty levels for Minesweeper.
Inputs: GameLogic, BoardManager
Outputs: AI moves (cell coordinates to uncover or flag)
External Sources: None
Author: Asa Maker
Creation Date: 2024-09-25
"""

import random
from enum import Enum
from typing import List, Optional, Tuple


class Difficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


class AISolver:
    def __init__(self, game, difficulty: Difficulty) -> None:
        """Initialize AI solver with game reference and difficulty."""
        self.game = game
        self.difficulty = difficulty
        self.board = game.board

    # ----------------------------
    # Turn orchestration
    # ----------------------------
    def make_move(self) -> Optional[Tuple[str, int, int]]:
        """Make exactly one turn-ending move.

        MEDIUM/HARD: repeatedly apply deductions; flags do NOT end the turn.
        The moment we perform an uncover, we end the turn and return it.
        If no deduction yields an uncover, fall back to an uncover (random/cheat).
        EASY: random uncover.
        """
        if self.difficulty == Difficulty.EASY:
            return self.easy_move()

        try_patterns = (self.difficulty == Difficulty.HARD)
        return self._move_until_uncover(try_patterns)

    def _move_until_uncover(self, try_patterns: bool) -> Optional[Tuple[str, int, int]]:
        """Run deduction steps; flags don't end the turn. Stop when we uncover."""
        # Safety cap to prevent infinite loops in edge cases
        for _ in range(100):
            move = self._deduction_step(try_patterns)
            if not move:
                break
            action, r, c = move
            if action == "uncover":
                # This ends the AI's turn
                return move
            # If we flagged, keep looping to try unlocking a safe uncover

        # CORRECTION: Couldn’t deduce an uncover — fall back to a random guess.
        # This makes the Hard AI fallible, matching the behavior in the screenshot.
        # Previously, Hard mode called self.cheat_move(), making it impossible to lose.
        return self.easy_move()

    def _deduction_step(self, try_patterns: bool) -> Optional[Tuple[str, int, int]]:
        """Perform a single deduction action (flag OR uncover) if available."""
        if try_patterns:
            move = self.apply_121_pattern()
            if move:
                return move
        return self.apply_basic_rules()

    # ----------------------------
    # Utility
    # ----------------------------
    def get_hidden_cells(self) -> List[Tuple[int, int]]:
        """Get all hidden (covered, unflagged) cells."""
        hidden_cells: List[Tuple[int, int]] = []
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cell(r, c)
                if cell.is_covered and not cell.flagged:
                    hidden_cells.append((r, c))
        return hidden_cells

    # ----------------------------
    # Base actions
    # ----------------------------
    def easy_move(self) -> Optional[Tuple[str, int, int]]:
        """Random cell selection, avoiding flagged/uncovered cells."""
        hidden_cells = self.get_hidden_cells()
        if hidden_cells:
            r, c = random.choice(hidden_cells)
            self.game.uncover_cell(r, c, is_ai_move=True)
            return "uncover", r, c
        return None

    def apply_basic_rules(self) -> Optional[Tuple[str, int, int]]:
        """Apply flagging and safe cell rules."""
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cell(r, c)

                # Only process uncovered cells with neighbor mines
                if not cell.is_covered and cell.neighbor_count > 0:
                    neighbors = self.board.neighbors(r, c)
                    hidden: List[Tuple[int, int]] = []
                    flagged: List[Tuple[int, int]] = []

                    for nr, nc in neighbors:
                        n_cell = self.board.cell(nr, nc)
                        if n_cell.is_covered:
                            if n_cell.flagged:
                                flagged.append((nr, nc))
                            else:
                                hidden.append((nr, nc))

                    # Rule 1: If (flagged + hidden) == number, all hidden are mines -> flag them
                    if hidden and (len(flagged) + len(hidden) == cell.neighbor_count):
                        for hr, hc in hidden:
                            if not self.board.cell(hr, hc).flagged:
                                self.game.toggle_flagged_cell(hr, hc, is_ai_move=True)
                                return "flag", hr, hc

                    # Rule 2: If flagged == number, the rest of hidden are safe -> uncover them
                    if len(flagged) == cell.neighbor_count and hidden:
                        for hr, hc in hidden:
                            self.game.uncover_cell(hr, hc, is_ai_move=True)
                            return "uncover", hr, hc
        return None

    # ----------------------------
    # Advanced pattern (HARD)
    # ----------------------------
    def apply_121_pattern(self) -> Optional[Tuple[str, int, int]]:
        """Detect and apply 1-2-1 pattern logic."""
        # Check horizontal patterns
        for r in range(self.board.rows):
            for c in range(1, self.board.cols - 1):
                move = self.check_and_apply_121_horizontal(r, c)
                if move:
                    return move

        # Check vertical patterns
        for r in range(1, self.board.rows - 1):
            for c in range(self.board.cols):
                move = self.check_and_apply_121_vertical(r, c)
                if move:
                    return move
        return None

    def check_and_apply_121_horizontal(self, r: int, c: int) -> Optional[Tuple[str, int, int]]:
        """Check and apply horizontal 1-2-1 pattern centered at (r, c)."""
        cells = [self.board.cell(r, c - 1), self.board.cell(r, c), self.board.cell(r, c + 1)]
        if (
            not cells[0].is_covered and cells[0].neighbor_count == 1
            and not cells[1].is_covered and cells[1].neighbor_count == 2
            and not cells[2].is_covered and cells[2].neighbor_count == 1
        ):
            for dr in (-1, 1):
                # Middle above/below is safe
                if self.board.in_bounds(r + dr, c):
                    middle_cell = self.board.cell(r + dr, c)
                    if middle_cell.is_covered and not middle_cell.flagged:
                        self.game.uncover_cell(r + dr, c, is_ai_move=True)
                        return "uncover", r + dr, c
                # Outer corners are mines
                for dc in (-1, 1):
                    if self.board.in_bounds(r + dr, c + dc):
                        outer_cell = self.board.cell(r + dr, c + dc)
                        if outer_cell.is_covered and not outer_cell.flagged:
                            self.game.toggle_flagged_cell(r + dr, c + dc, is_ai_move=True)
                            return "flag", r + dr, c + dc
        return None

    def check_and_apply_121_vertical(self, r: int, c: int) -> Optional[Tuple[str, int, int]]:
        """Check and apply vertical 1-2-1 pattern centered at (r, c)."""
        cells = [self.board.cell(r - 1, c), self.board.cell(r, c), self.board.cell(r + 1, c)]
        if (
            not cells[0].is_covered and cells[0].neighbor_count == 1
            and not cells[1].is_covered and cells[1].neighbor_count == 2
            and not cells[2].is_covered and cells[2].neighbor_count == 1
        ):
            for dc in (-1, 1):
                # Middle left/right is safe
                if self.board.in_bounds(r, c + dc):
                    middle_cell = self.board.cell(r, c + dc)
                    if middle_cell.is_covered and not middle_cell.flagged:
                        self.game.uncover_cell(r, c + dc, is_ai_move=True)
                        return "uncover", r, c + dc
                # Outer corners are mines
                for dr in (-1, 1):
                    if self.board.in_bounds(r + dr, c + dc):
                        outer_cell = self.board.cell(r + dr, c + dc)
                        if outer_cell.is_covered and not outer_cell.flagged:
                            self.game.toggle_flagged_cell(r + dr, c + dc, is_ai_move=True)
                            return "flag", r + dr, c + dc
        return None

    # ----------------------------
    # Hard fallback (cheat) - Now Unused
    # ----------------------------
    def cheat_move(self) -> Optional[Tuple[str, int, int]]:
        """Hard mode cheat - always uncover a safe cell."""
        safe_cells: List[Tuple[int, int]] = []
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cell(r, c)
                if cell.is_covered and not cell.flagged and not cell.is_mine:
                    safe_cells.append((r, c))
        if safe_cells:
            r, c = random.choice(safe_cells)
            self.game.uncover_cell(r, c, is_ai_move=True)
            return "uncover", r, c
        return None