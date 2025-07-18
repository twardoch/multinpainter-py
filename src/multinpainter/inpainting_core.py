from collections import OrderedDict
import logging
from typing import Tuple

from PIL import Image

def calculate_expansion(
    center_of_focus: Tuple[int, int],
    input_width: int,
    input_height: int,
    out_width: int,
    out_height: int,
) -> Tuple[int, int, int, int]:
    x_percentage = center_of_focus[0] / input_width
    y_percentage = center_of_focus[1] / input_height

    x_left = int((out_width - input_width) * x_percentage)
    x_right = out_width - input_width - x_left
    y_top = int((out_height - input_height) * y_percentage)
    y_bottom = out_height - input_height - y_top

    return x_left, x_right, y_top, y_bottom


def paste_input_image(
    out_image: Image.Image, input_image: Image.Image, expansion: Tuple[int, int, int, int]
) -> None:
    out_image.paste(input_image, (expansion[0], expansion[2]))


def get_initial_square_position(
    expansion: Tuple[int, int, int, int],
    square: int,
    input_width: int,
    input_height: int,
) -> Tuple[int, int]:
    x_init = max(0, expansion[0] - (square - input_width) // 2)
    y_init = max(0, expansion[2] - (square - input_height) // 2)
    return x_init, y_init


def create_planned_squares(
    initial_square_position: Tuple[int, int],
    square_size: int,
    step_size: int,
    out_width: int,
    out_height: int,
) -> OrderedDict:
    """
    Generates a dictionary that represents the order in which the image squares will be processed during the inpainting process.
    The dictionary has the following keys:
    - `init`: contains the initial square position.
    - `up`: contains the squares above the initial square, in the order they should be processed.
    - `left`: contains the squares to the left of the initial square, in the order they should be processed.
    - `right`: contains the squares to the right of the initial square, in the order they should be processed.
    - `down`: contains the squares below the initial square, in the order they should be processed.
    - `up_left`: contains the squares above and to the left of the initial square, in the order they should be processed.
    - `up_right`: contains the squares above and to the right of the initial square, in the order they should be processed.
    - `down_left`: contains the squares below and to the left of the initial square, in the order they should be processed.
    - `down_right`: contains the squares below and to the right of the initial square, in the order they should be processed.

    Each key in the dictionary is associated with a list of square positions that represent the order in which the inpainting process will occur.
    The order is determined by starting from the initial square and iterating over each direction (up, down, left, right) until there is no more space in that direction.
    Then, for each combination of up/down and left/right directions, the squares are ordered diagonally.

    Returns:
    The generated dictionary.
    """

    init_square = initial_square_position

    planned_squares = OrderedDict(
        init=[init_square],
        up=[],
        left=[],
        right=[],
        down=[],
        up_left=[],
        up_right=[],
        down_left=[],
        down_right=[],
    )

    # Calculate up, left, right, and down squares
    x, y = init_square
    for direction in ["up", "left", "right", "down"]:
        cur_x, cur_y = x, y
        while True:
            cur_x, cur_y = move_square((cur_x, cur_y), direction, step_size, out_width, out_height, square_size)
            if cur_x is None or cur_y is None:
                break
            planned_squares[direction].append((cur_x, cur_y))

    # Calculate up_left, up_right, down_left, and down_right squares
    for up_down in ["up", "down"]:
        for left_right in ["left", "right"]:
            quadrant = f"{up_down}_{left_right}"
            for up_sq in planned_squares[up_down]:
                for lr_sq in planned_squares[left_right]:
                    quadrant_sq = (lr_sq[0], up_sq[1])
                    planned_squares[quadrant].append(quadrant_sq)

    logging.info(f"Planned squares: {planned_squares}")
    return planned_squares


def move_square(
    square_delta: Tuple[int, int], direction: str, step: int, out_width: int, out_height: int, square: int
) -> Tuple[int, int]:
    """
    Calculates the position of the square in a given direction.

    Args:
    - square_delta: A tuple (x, y) representing the position of the square.
    - direction: A string representing the direction of the movement. Can be one of 'up', 'down', 'left', 'right'.

    Returns:
    - A tuple (x, y) representing the new position of the square after the movement in the given direction.
    - If the new position is outside the image, the corresponding coordinate is set to None.
    """

    x, y = square_delta

    if direction == "up":
        next_y = max(0, y - step)
        if next_y == y:
            return x, None
        return x, next_y
    elif direction == "left":
        next_x = max(0, x - step)
        if next_x == x:
            return None, y
        return next_x, y
    elif direction == "right":
        next_x = min(x + step, out_width - square)
        if next_x == x:
            return None, y
        return next_x, y
    elif direction == "down":
        next_y = min(y + step, out_height - square)
        if next_y == y:
            return x, None
        return x, next_y
