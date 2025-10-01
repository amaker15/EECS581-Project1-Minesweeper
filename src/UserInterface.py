"""
Module: UserInterface
Description: Render User Interface, send user input to input handler, display board with labels.
Inputs: GameState, Board, GameLogic
Outputs: User Input (click type, (x, y))
External Sources: None
Author: Hale Coffman
Creation Date: 2024-09-07
"""

import os
import sys
from typing import Dict, Tuple

import pygame

from GameLogic import GameLogic, GameMode
from InputHandler import InputHandler

game = GameLogic()
input_handler = InputHandler()

# Game variables
SCREEN_WIDTH = 1200
SCREEN_LENGTH = 850  # Increased for labels
CELL_SIZE = (32, 32)
DISTANCE_BETWEEN_CELLS = 36
BOARD_SIZE = 10
BOARD_DISTANCE_DOWN = 350  # Adjusted for labels
BOARD_DISTANCE_LEFT = (SCREEN_WIDTH // 2) - int(DISTANCE_BETWEEN_CELLS * (BOARD_SIZE / 2)) - 20  # Adjusted for labels

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
GREEN = (50, 200, 50)

# Initialize UI
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_LENGTH))
pygame.display.set_caption("MineSweeper - Enhanced Edition")
screen.fill("white")
clock = pygame.time.Clock()

# Fonts
title_font = pygame.font.SysFont("arialblack", 60)
mine_count_font = pygame.font.SysFont("arialblack", 15)
mine_prompt_font = pygame.font.SysFont("arialblack", 15)
win_loss_font = pygame.font.SysFont("arialblack", 30)
label_font = pygame.font.SysFont("arial", 14)
timer_font = pygame.font.SysFont("arialblack", 20)
hint_font_small = pygame.font.SysFont("arialblack", 14)


def resource_path(rel_path: str) -> str:
    """Return an absolute path to a resource."""
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, rel_path)


def load_assets() -> Dict[str, pygame.Surface]:
    """Load all assets."""
    assets: Dict[str, pygame.Surface] = {}
    pngs = [
        "tile",
        "unexplored_tile",
        "mine",
        "flagged_tile",
        "exploding_mine",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
    ]
    for png in pngs:
        path = resource_path(os.path.join("assets", f"{png}.png"))
        asset = pygame.image.load(path)
        asset = pygame.transform.scale(asset, CELL_SIZE)
        assets[png] = asset
    return assets

def current_mode_label() -> str:
    """Return the numbered label matching the start-menu options."""
    if game.game_mode == GameMode.HUMAN:
        return "1. Human Only"

    if game.game_mode == GameMode.VERSUS:
        if game.ai_difficulty == "easy":
            return "2. Human vs AI (Easy)"
        if game.ai_difficulty == "medium":
            return "3. Human vs AI (Medium)"
        if game.ai_difficulty == "hard":
            return "4. Human vs AI (Hard)"

    if game.game_mode == GameMode.AI:
        if game.ai_difficulty == "easy":
            return "5. AI Only (Easy)"
        if game.ai_difficulty == "medium":
            return "6. AI Only (Medium)"
        if game.ai_difficulty == "hard":
            return "7. AI Only (Hard)"

    # Fallback
    return "Unknown Mode"


def render_board_labels() -> None:
    """Render column (A-J) and row (1-10) labels."""
    # Column labels (A-J)
    for col in range(10):
        letter = chr(ord("A") + col)
        text = label_font.render(letter, True, BLACK)
        x = BOARD_DISTANCE_LEFT + col * DISTANCE_BETWEEN_CELLS + DISTANCE_BETWEEN_CELLS // 2 - 5
        y = BOARD_DISTANCE_DOWN - 25
        screen.blit(text, (x, y))

    # Row labels (1-10)
    for row in range(10):
        number = str(row + 1)
        text = label_font.render(number, True, BLACK)
        x = BOARD_DISTANCE_LEFT - 25
        y = BOARD_DISTANCE_DOWN + row * DISTANCE_BETWEEN_CELLS + DISTANCE_BETWEEN_CELLS // 2 - 7
        screen.blit(text, (x, y))


def render_board() -> None:
    """Render the game board with all cells.
    - Draws covered/uncovered/flagged states
    - Reveals all mines on EndWin/EndLose
    - Highlights the current hint ONLY while Playing
    """
    y = BOARD_DISTANCE_DOWN
    for row in range(10):
        x = BOARD_DISTANCE_LEFT
        for col in range(10):
            if game.state.name == "Start":
                # On the Start screen, just show unexplored tiles
                screen.blit(assets["unexplored_tile"], (x, y))
            else:
                cell = game.board.grid[row][col]

                if cell.flagged:
                    screen.blit(assets["flagged_tile"], (x, y))
                elif cell.is_covered:
                    screen.blit(assets["unexplored_tile"], (x, y))
                elif cell.neighbor_count > 0:
                    screen.blit(assets[str(cell.neighbor_count)], (x, y))
                else:
                    # Uncovered with zero neighbors
                    screen.blit(assets["tile"], (x, y))

                # Reveal all mines after game over/win
                if game.state.name in ("EndLose", "EndWin") and cell.is_mine:
                    screen.blit(assets["tile"], (x, y))
                    screen.blit(assets["mine"], (x, y))

            # Draw hint outline on top (only while actively playing)
            if game.state.name == "Playing" and getattr(game, "last_hint", None) == (row, col):
                pygame.draw.rect(
                    screen,
                    GREEN,
                    (x - 2, y - 2, CELL_SIZE[0] + 4, CELL_SIZE[1] + 4),
                    2,
                )

            x += DISTANCE_BETWEEN_CELLS
        y += DISTANCE_BETWEEN_CELLS


def coords_to_index(coords: Tuple[int, int]):
    """Convert mouse coordinates to board indices - returns (row, col)."""
    x_start = BOARD_DISTANCE_LEFT
    y_start = BOARD_DISTANCE_DOWN

    x_click, y_click = coords
    col = int((x_click - x_start) // DISTANCE_BETWEEN_CELLS)
    row = int((y_click - y_start) // DISTANCE_BETWEEN_CELLS)

    # If clicked within grid return coords
    if 0 <= row <= 9 and 0 <= col <= 9:
        return row, col
    return False


def restart_to_start() -> None:
    """Return to the Start screen."""
    global game, text, message, cover_color, input_mode, ai_selected
    game.reset_game()
    text = ""
    message = ""
    cover_color = "BLACK"
    input_mode = "mines"
    ai_selected = False
    render_ui()


def draw_title() -> None:
    """Draw the game title."""
    title_text = "Minesweeper Enhanced"
    title_surface = title_font.render(title_text, True, RED)
    shadow_surface = title_font.render(title_text, True, BLACK)
    title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 90))
    shadow_rect = shadow_surface.get_rect(center=(SCREEN_WIDTH // 2 + 2, 92))
    screen.blit(shadow_surface, shadow_rect)
    screen.blit(title_surface, title_rect)


def update_mine_counter() -> None:
    """Update the mine counter display."""
    text = f"Mines Remaining: {game.flags_remaining}"
    mine_counter = mine_count_font.render(text, True, BLACK)
    mine_counter_rect = mine_counter.get_rect(center=(SCREEN_WIDTH // 2 - 100, 175))
    pygame.draw.rect(screen, WHITE, mine_counter_rect, 10)
    screen.blit(mine_counter, mine_counter_rect)


def render_timer() -> None:
    """Render the game timer."""
    if game.state.name in ("Playing", "EndWin", "EndLose"):
        duration = game.get_game_duration()
        minutes = duration // 60
        seconds = duration % 60
        timer_text = f"Time: {minutes:02d}:{seconds:02d}"
        timer_surface = timer_font.render(timer_text, True, BLACK)
        timer_rect = timer_surface.get_rect(center=(SCREEN_WIDTH // 2 + 100, 175))
        screen.blit(timer_surface, timer_rect)


def render_hint_counter() -> None:
    """Render the hint counter."""
    if game.state.name == "Playing":
        hint_text = f"Hints: {game.hints_remaining} (Press H)"
        hint_surface = hint_font_small.render(hint_text, True, BLUE)
        hint_rect = hint_surface.get_rect(center=(SCREEN_WIDTH // 2, 210))
        screen.blit(hint_surface, hint_rect)


def render_ai_status() -> None:
    """Render mode and (if applicable) turn status."""
    # Show the playing mode while the game is running or finished
    if game.state.name in ("Playing", "EndWin", "EndLose"):
        mode_text = f"Playing: {current_mode_label()}"
        mode_surface = mine_count_font.render(mode_text, True, BLACK)
        mode_rect = mode_surface.get_rect(center=(SCREEN_WIDTH // 2, 240))
        screen.blit(mode_surface, mode_rect)

    # In Versus mode show whose turn it is
    if game.game_mode == GameMode.VERSUS and game.state.name == "Playing":
        turn_text = f"Current Turn: {'Human' if game.current_turn == 'human' else 'AI'}"
        turn_surface = mine_count_font.render(
            turn_text,
            True,
            (50, 200, 50) if game.current_turn == "human" else (200, 50, 50),
        )
        turn_rect = turn_surface.get_rect(center=(SCREEN_WIDTH // 2, 260))
        screen.blit(turn_surface, turn_rect)


def render_win_or_loss() -> None:
    """Render win/loss message."""
    if game.state.name == "EndLose":
        title = "YOU LOSE :("
    elif game.state.name == "EndWin":
        title = "YOU WIN :)"
    else:
        return

    result = win_loss_font.render(title, True, BLACK)
    result_rect = result.get_rect(center=(SCREEN_WIDTH // 2, 280))
    screen.blit(result, result_rect)

    hint_font = pygame.font.SysFont("arialblack", 20)
    hint = hint_font.render("Press R to restart", True, BLACK)
    screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 315)))


def render_ui() -> None:
    """Render the complete UI.

    On the Start screen, only show the title (the start menu is drawn by
    render_start_ui). Once the game is Playing/Ended, draw the board + HUD.
    """
    screen.fill(WHITE)
    draw_title()

    # Don't draw the board or HUD while on the Start screen
    if game.state.name == "Start":
        return

    # Game is running or ended — render board and HUD
    render_board_labels()
    render_board()

    # Show mines remaining only after the game has started
    if game.state.name in ("Playing", "EndWin", "EndLose"):
        update_mine_counter()

    render_timer()
    render_hint_counter()
    render_ai_status()
    render_win_or_loss()



def render_start_ui(text: str, message: str, cover_color: str, input_mode: str) -> None:
    """Render the start screen UI."""
    # Display error message if any
    if message:
        message_box = mine_prompt_font.render(message, True, RED)
        message_rect = message_box.get_rect(center=(SCREEN_WIDTH // 2, 700))
        screen.blit(message_box, message_rect)

    if input_mode == "mines":
        # Mine input prompt
        label = mine_prompt_font.render("Enter number of mines (10-20), then press ENTER:", True, cover_color)
        label_rect = label.get_rect(center=(SCREEN_WIDTH // 2, 220))
        screen.blit(label, label_rect)

        # Draw input text box
        mine_input_box = pygame.Rect(SCREEN_WIDTH // 2 - 70, 250, 140, 40)
        pygame.draw.rect(screen, cover_color, mine_input_box, 2)

        # Render text inside the box
        txt_surface = mine_prompt_font.render(text, True, BLACK)
        text_rect = txt_surface.get_rect(center=(SCREEN_WIDTH // 2, 265))
        screen.blit(txt_surface, text_rect)

    elif input_mode == "ai_mode":
        # AI mode selection
        label = mine_prompt_font.render("Select Game Mode:", True, BLACK)
        label_rect = label.get_rect(center=(SCREEN_WIDTH // 2, 220))
        screen.blit(label, label_rect)

        modes = [
            "1 - Human Only",
            "2 - Human vs AI (Easy)",
            "3 - Human vs AI (Medium)",
            "4 - Human vs AI (Hard)",
            "5 - AI Only (Easy)",
            "6 - AI Only (Medium)",
            "7 - AI Only (Hard)",
        ]

        y_offset = 250
        for mode in modes:
            mode_text = mine_prompt_font.render(mode, True, BLACK)
            mode_rect = mode_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            screen.blit(mode_text, mode_rect)
            y_offset += 30


# Initialize variables
text = ""
message = ""
cover_color = "BLACK"
input_mode = "mines"  # 'mines' or 'ai_mode'
ai_selected = False
ai_move_delay = 0
last_ai_move_time = 0

assets = load_assets()
render_ui()

running = True
while running:
    current_time = pygame.time.get_ticks()

    # Handle AI moves in AI-only mode or AI's turn in VERSUS mode
    if game.state.name == "Playing":
        if game.game_mode == GameMode.AI:
            # AI-only mode - make moves automatically
            if current_time - last_ai_move_time > 500:  # 500ms delay between moves
                if game.ai_solver:
                    move = game.ai_solver.make_move()
                    if move:
                        render_ui()
                        last_ai_move_time = current_time
        elif game.game_mode == GameMode.VERSUS and game.current_turn == "ai":
            if current_time - last_ai_move_time > 1000:
                if game.ai_solver:
                    move = game.ai_solver.make_move()
                    if move:
                        # Only switch if game not ended by the AI move
                        if game.state.name == "Playing":
                            game.switch_turn()
                        render_ui()
                        last_ai_move_time = current_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game.state.name == "Start":
            render_ui()

            if event.type == pygame.KEYDOWN:
                if input_mode == "mines":
                    response = input_handler.handle_keyboard_input(game, event, text, "mines")
                    if response.response_code.value == 0:
                        # Mines set successfully
                        text = ""
                        input_mode = "ai_mode"
                        render_ui()
                    elif response.response_code.value == 1:
                        # Invalid input
                        message = response.message
                        text = ""
                    else:
                        text = response.message

                elif input_mode == "ai_mode":
                    response = input_handler.handle_ai_mode_input(game, event, text)

                    if response.response_code.value == 0:  # Mode selected
                        cover_color = "WHITE"
                        text = "Game Started!"
                        game.start_game()  # switch state first
                        last_ai_move_time = current_time
                        render_ui()  # now draws the Playing UI

            # Only draw the start menu if we are still on the Start screen
            if game.state.name == "Start":
                if input_mode == 'mines':
                    render_start_ui(text, message, cover_color, 'mines')
                elif input_mode == 'ai_mode':
                    render_start_ui(text, message, cover_color, 'ai_mode')


        elif game.state.name == "Playing":
            # Handle hint request
            if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                hint = game.use_hint()
                if hint:
                    row, col = hint
                    game.last_hint = (row, col)  # type: ignore[attr-defined]
                    # Highlight the hint cell
                    render_ui()

            # Handle mouse clicks (disabled in AI-only)
            if event.type == pygame.MOUSEBUTTONDOWN and game.game_mode != GameMode.AI:
                coords = coords_to_index(event.pos)
                if coords:
                    row, col = coords  # Now correctly ordered
                    response = input_handler.handle_click(game, event, row, col)
                    render_ui()

        elif game.state.name in ("EndLose", "EndWin"):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                restart_to_start()
                render_ui()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
