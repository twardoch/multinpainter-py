import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Tuple

from PIL import Image


def to_rgba(image: Image) -> Image:
    """
    Converts the given image to RGBA format and returns the converted image.

    Args:
        image (Image): The input image to be converted.

    Returns:
        Image: The converted RGBA image.
    """
    return image.convert("RGBA")


def timestamp() -> str:
    """
    Returns the current timestamp in the format 'YYYYMMDD-HHMMSS'.

    Returns:
        str: The current timestamp as a string.
    """
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def snapshot(image: Image, out_path: Path, timestamp_func: Callable, verbose: bool) -> None:
    """
    Saves a snapshot of the current output image with a timestamp in the file name. Only saves the snapshot if the verbose flag is set to True.

    Args:
        image (Image): The image to save.
        out_path (Path): The base path for the output image.
        timestamp_func (Callable): A function that returns a timestamp string.
        verbose (bool): Whether verbose logging is enabled.
    """
    if verbose:
        snapshot_path = Path(
            out_path.parent,
            f"{out_path.stem}-{timestamp_func()}.png",
        )
        logging.info(f"Saving snapshot: {snapshot_path}")
        image.save(
            snapshot_path,
            format="PNG",
        )


def open_image(image_path: Path) -> Tuple[Image.Image, int, int]:
    """
    Opens the input image from the specified image path, converts it to RGBA format, and returns the image and its dimensions.

    Args:
        image_path (Path): The path to the input image file.

    Returns:
        Tuple[Image.Image, int, int]: A tuple containing the Image object, its width, and its height.
    """
    image = to_rgba(Image.open(image_path))
    input_width, input_height = image.size
    logging.info(f"Input size: {input_width}x{input_height}")
    return image, input_width, input_height


def save_image(image: Image.Image, out_path: Path) -> None:
    """
    Saves the output image to the specified output path with a PNG format.

    Args:
        image (Image.Image): The image to save.
        out_path (Path): The path to save the image to.
    """
    image.save(out_path.with_suffix(".png"), format="PNG")
    logging.info(f"Output image saved to: {out_path}")
