from typing import Tuple

def human_in_square(square_box: Tuple[int, int, int, int], human_boxes: list[Tuple[int, int, int, int]]) -> bool:
    """
    Determines whether any detected human bounding boxes intersect with the given square_box.

    Args:
        square_box (Tuple[int, int, int, int]): The (x0, y0, x1, y1) coordinates of the square_box.
        human_boxes (list[Tuple[int, int, int, int]]): List of bounding boxes for detected humans.

    Returns:
        bool: True if any detected human bounding boxes intersect with the square_box, False otherwise.
    """
    x0, y0, x1, y1 = square_box

    for box in human_boxes:
        bx0, by0, bx1, by1 = box
        if x0 < bx1 and x1 > bx0 and y0 < by1 and y1 > by0:
            return True
    return False
