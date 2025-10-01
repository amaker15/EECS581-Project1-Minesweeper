"""
Module: GameLogic
Description: Handles base game functionality and management of state.
Inputs: None
Outputs: None
External sources: None
Author: Aryan Kevat
Creation Date: 2024-09-05
"""

import enum
import random
import time
from typing import List, Optional, Tuple

from BoardManager import BoardManager


class GameState(enum.Enum):
    Start = 0
    Playing = 1
    EndWin = 2
    EndLose = 3


class EndCondition(enum.Enum):
    Win = True
    Loss = False


class ToggleMine(enum.Enum):
    Place = 1
    Remove = -1


class GameMode(enum.Enum):
    HUMAN = 0
    AI = 1
    VERSUS = 2  # Human vs AI taking turns


class GameLogic:
    def __init__(self) -> None:
        self.state: GameState = GameState.Start
        self.total_mines: int = 0
        self.flags_remaining: int = 0
        self.board = BoardManager()
        self.covered_cells: int = self.board.rows * self.board.cols
        self.game_mode = GameMode.HUMAN
        self.current_turn: str = "human"  # 'human' or 'ai'
        self.ai_solver = None
        self.ai_difficulty: Optional[str] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.hints_remaining: int = 3  # Custom feature: hint system
        self.moves_history: List[Tuple[str, int, int, bool]] = []  # Track all moves for replay
        self.last_hint: Optional[Tuple[int, int]] = None  # UI highlight for most recent hint

    def set_mines(self, mines: int) -> None:
        """Set the total number of mines to be placed."""
        self.total_mines = mines
        self.flags_remaining = mines

    def set_game_mode(self, mode: GameMode, ai_difficulty: Optional[str] = None) -> None:
        """Set the game mode and AI difficulty if applicable."""
        self.game_mode = mode
        self.ai_difficulty = ai_difficulty
        if mode in [GameMode.AI, GameMode.VERSUS]:
            from AISolver import AISolver, Difficulty

            diff_map = {
                "easy": Difficulty.EASY,
                "medium": Difficulty.MEDIUM,
                "hard": Difficulty.HARD,
            }
            self.ai_solver = AISolver(self, diff_map.get(ai_difficulty, Difficulty.EASY))

    def start_game(self) -> None:
        """Move the game to the playing state and place mines."""
        self.state = GameState.Playing
        self.start_time = time.time()
        self.initialize_board()

    def end_game(self, condition: EndCondition) -> None:
        """Ends game based on passed condition."""
        self.end_time = time.time()
        self.state = GameState.EndWin if condition == EndCondition.Win else GameState.EndLose
        # Clear any lingering hint highlight
        self.last_hint = None

    def get_game_duration(self) -> int:
        """Get the duration of the game in seconds (rounded down)."""
        if self.start_time:
            if self.end_time:
                return int(self.end_time - self.start_time)
            return int(time.time() - self.start_time)
        return 0

    def reset_game(self) -> None:
        """Reset the game state and the board state."""
        self.board.reset()
        self.state = GameState.Start
        self.total_mines = 0
        self.flags_remaining = 0
        self.covered_cells = self.board.rows * self.board.cols
        self.current_turn = "human"
        self.start_time = None
        self.end_time = None
        self.hints_remaining = 3
        self.moves_history = []
        self.last_hint = None

    def initialize_board(self) -> None:
        """Sample and place mines in random locations."""
        # Properly place mines using row/col coordinates
        all_positions = [(r, c) for r in range(self.board.rows) for c in range(self.board.cols)]
        mine_positions = random.sample(all_positions, k=self.total_mines)
        for row, col in mine_positions:
            self.board.toggle_mine(row, col)

    def uncover_first_cell(self, old_row: int, old_col: int) -> None:
        """Safely uncover the first cell (guarantee first click is not a mine)."""
        # Continue normal processing if the cell is already safe
        if not self.board.cell(old_row, old_col).is_mine:
            return

        # Move the mine elsewhere
        while True:
            new_row = random.randrange(self.board.rows)
            new_col = random.randrange(self.board.cols)
            new_cell = self.board.cell(new_row, new_col)
            if not new_cell.is_mine:
                self.board.toggle_mine(new_row, new_col)  # place a mine at the new location
                break
        self.board.toggle_mine(old_row, old_col)  # remove mine from original location

    def uncover_cell(self, row: int, col: int, is_ai_move: bool = False) -> bool:
        """Uncover a selected cell.

        Returns:
            bool: True if this call resulted in an uncover or game end; False if no-op
                  (e.g., clicking an already-opened or flagged cell).
        """
        cell = self.board.cell(row, col)

        # No-op clicks
        if not cell.is_covered:
            return False
        if cell.flagged:
            return False

        # Track move
        self.moves_history.append(("uncover", row, col, is_ai_move))

        # Special handling for the very first uncover to guarantee safety
        if self.covered_cells == (self.board.rows * self.board.cols):
            self.uncover_first_cell(row, col)
            cell = self.board.cell(row, col)  # refresh after potential mine relocation

        if cell.is_mine:
            # In Versus mode, the mover who hits a mine loses => other side wins.
            if self.game_mode == GameMode.VERSUS:
                self.end_game(EndCondition.Win if is_ai_move else EndCondition.Loss)
            else:
                # HUMAN-only or AI-only: treat a mine as a loss for the single player session
                self.end_game(EndCondition.Loss)
            return True

        # Uncover the cell
        self.board.uncover(row, col)
        self.covered_cells -= 1

        # If this was the hinted cell, clear the highlight
        if self.last_hint == (row, col):
            self.last_hint = None

        # Flood fill for zeros
        if cell.neighbor_count == 0:
            for i in range(row - 1, row + 2):
                for j in range(col - 1, col + 2):
                    if not self.board.in_bounds(i, j):
                        continue
                    n_cell = self.board.cell(i, j)
                    if n_cell.is_covered and not n_cell.is_mine:
                        # Note: we ignore the return value of recursive calls
                        self.uncover_cell(i, j, is_ai_move)

        # Win check: all non-mine cells uncovered
        if self.covered_cells == self.total_mines:
            self.end_game(EndCondition.Win)

        return True

    def toggle_flagged_cell(self, row: int, col: int, is_ai_move: bool = False) -> None:
        """Toggle flagged state with flag count validation."""
        cell = self.board.cell(row, col)
        if not cell.is_covered:
            return

        # Track move
        self.moves_history.append(("flag", row, col, is_ai_move))

        if cell.flagged:
            self.board.set_flag(row, col, False)
            self.flags_remaining += 1
        elif self.flags_remaining > 0:
            self.board.set_flag(row, col, True)
            self.flags_remaining -= 1

    def use_hint(self) -> Optional[Tuple[int, int]]:
        """Custom feature: Reveal a safe cell (limited uses). Returns (row, col) or None."""
        if self.hints_remaining <= 0:
            return None

        # Find all safe covered cells
        safe_cells: List[Tuple[int, int]] = []
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                ccell = self.board.cell(r, c)
                if ccell.is_covered and not ccell.is_mine and not ccell.flagged:
                    safe_cells.append((r, c))

        if safe_cells:
            self.hints_remaining -= 1
            row, col = random.choice(safe_cells)
            self.last_hint = (row, col)  # store so UI can highlight
            return row, col
        return None

    def switch_turn(self) -> None:
        """Switch between human and AI turns in VERSUS mode."""
        if self.game_mode == GameMode.VERSUS and self.state == GameState.Playing:
            self.current_turn = "ai" if self.current_turn == "human" else "human"
