"""
Module: InputHandler
Description: Contains InputHandler class with functions that handle user clicks and keyboard
inputs and returns updated game state and the type of response that was given.
Inputs: None
Outputs: None
External Sources: None
Author: Sam Suggs
Creation Date: 2024-09-10
"""

import enum
from typing import Optional

import pygame

from GameLogic import GameLogic, GameMode, GameState


class ResponseCode(enum.Enum):
    Finished = 0
    Failed = 1
    InProgress = 2
    Ignored = 3


class Response:
    """Package and send input handling results."""

    def __init__(self, game: GameLogic, response_code: ResponseCode, message: str = "") -> None:
        self.game: GameLogic = game
        self.response_code: ResponseCode = response_code
        self.message: str = message


class InputHandler:
    """Handles keyboard and mouse input."""

    # Keyboard input handling for mine count and AI mode selection
    def handle_keyboard_input(self, game: GameLogic, event, text: str, input_mode: str = "mines") -> Response:
        """Handle keyboard input for mine count or AI mode selection."""
        if game.state != GameState.Start:
            return Response(game, ResponseCode.Ignored, "Game must be in starting state")

        if event.type == pygame.KEYDOWN:
            if input_mode == "mines":
                return self.handle_mine_input(game, event, text)
            if input_mode == "ai_mode":
                return self.handle_ai_mode_input(game, event, text)

        return Response(game, ResponseCode.Ignored, "Ignored irrelevant input")

    def handle_mine_input(self, game: GameLogic, event, text: str) -> Response:
        """Handle mine count input."""
        if event.key == pygame.K_RETURN:
            if text.isdigit():
                mines = int(text)
                if 10 <= mines <= 20:
                    game.set_mines(mines)
                    return Response(game, ResponseCode.Finished, f"Set {mines} mines")
                return Response(game, ResponseCode.Failed, "Mine count must be between 10 and 20")
            return Response(game, ResponseCode.Failed, "Input must be a number between 10 and 20")
        if event.key == pygame.K_BACKSPACE:
            text = text[:-1]
            return Response(game, ResponseCode.InProgress, text)

        text += event.unicode
        return Response(game, ResponseCode.InProgress, text)

    def handle_ai_mode_input(self, game: GameLogic, event, text: str) -> Response:
        """Handle AI mode selection."""
        if event.key == pygame.K_1:
            game.set_game_mode(GameMode.HUMAN)
            return Response(game, ResponseCode.Finished, "Human mode selected")
        if event.key == pygame.K_2:
            game.set_game_mode(GameMode.VERSUS, "easy")
            return Response(game, ResponseCode.Finished, "Versus AI (Easy) selected")
        if event.key == pygame.K_3:
            game.set_game_mode(GameMode.VERSUS, "medium")
            return Response(game, ResponseCode.Finished, "Versus AI (Medium) selected")
        if event.key == pygame.K_4:
            game.set_game_mode(GameMode.VERSUS, "hard")
            return Response(game, ResponseCode.Finished, "Versus AI (Hard) selected")
        if event.key == pygame.K_5:
            game.set_game_mode(GameMode.AI, "easy")
            return Response(game, ResponseCode.Finished, "AI Only (Easy) selected")
        if event.key == pygame.K_6:
            game.set_game_mode(GameMode.AI, "medium")
            return Response(game, ResponseCode.Finished, "AI Only (Medium) selected")
        if event.key == pygame.K_7:
            game.set_game_mode(GameMode.AI, "hard")
            return Response(game, ResponseCode.Finished, "AI Only (Hard) selected")

        return Response(game, ResponseCode.InProgress, "Select mode (1-7)")

    # Function to handle mouse clicks - turn only advances on a real uncover
    def handle_click(self, game: GameLogic, event, row: int, col: int) -> Response:
        """Handle mouse clicks with corrected coordinate order."""
        # Click inputs will only be handled when the game is in progress
        if game.state != GameState.Playing:
            return Response(game, ResponseCode.Ignored, "Game must be in progress")

        # Check if it's the human's turn in VERSUS mode
        if game.game_mode == GameMode.VERSUS and game.current_turn != "human":
            return Response(game, ResponseCode.Ignored, "Not human's turn")

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Left click -> uncover; only switch turns if uncover actually happened
                did_uncover = game.uncover_cell(row=row, col=col)

                # If we just opened the hinted cell, remove the highlight
                if getattr(game, "last_hint", None) == (row, col) and did_uncover:
                    game.last_hint = None

                # Only switch turns if the game is still running and the move was effective
                if game.game_mode == GameMode.VERSUS and game.state.name == "Playing" and did_uncover:
                    game.switch_turn()
                return Response(game, ResponseCode.Finished, f"Uncovered cell at ({col}, {row})")

            if event.button == 3:
                # Right click -> toggle flag (does not end turn)
                game.toggle_flagged_cell(row=row, col=col)
                return Response(game, ResponseCode.Finished, f"Toggled flag at ({col}, {row})")

            return Response(game, ResponseCode.Ignored, "Ignored irrelevant input")

        return Response(game, ResponseCode.Ignored, "Ignored irrelevant input")

    def handle_hint_request(self, game: GameLogic, event) -> Response:
        """Handle hint request (H key)."""
        if game.state != GameState.Playing:
            return Response(game, ResponseCode.Ignored, "Game must be in progress")

        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            hint = game.use_hint()
            if hint:
                row, col = hint
                return Response(game, ResponseCode.Finished, f"Hint: Safe cell at ({col}, {row})")
            return Response(game, ResponseCode.Failed, "No hints remaining or no safe cells")

        return Response(game, ResponseCode.Ignored, "Ignored irrelevant input")
