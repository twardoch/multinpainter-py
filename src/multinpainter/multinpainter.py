import io
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from collections import OrderedDict
from typing import Optional, Union, Tuple

import numpy as np
import openai
import requests
from PIL import Image
from progress.bar import Bar

from multinpainter import __version__

__author__ = "Adam Twardoch"
__license__ = "Apache-2.0"


def read_prompt(png_path: Union[str, Path]) -> Optional[str]:
    """
    Reads the prompt from the corresponding JSON file of the input image.

    Args:
        png_path (Union[str, Path]): The path of the input image file in PNG format.

    Returns:
        Optional[str]: The prompt text if the JSON file is found and contains a valid prompt, otherwise None.
    """
    with open(f"{Path(png_path).stem}.json") as f:
        prompt = json.load(f)["prompt"]
    logging.info(f"""read_prompt: {prompt}""")
    return prompt


class Multinpainter_OpenAI:
    """
    A class for iterative inpainting using OpenAI's Dall-E 2 and GPT-3 atificial intelligence models to extend (outpaint) an existing image to new defined dimensions. 

    Args:
        image_path (str): Path to the input image file.
        out_path (str): Path to save the output image file.
        out_width (int): Desired width of the output image.
        out_height (int): Desired height of the output image.
        prompt (str): Prompt for the GPT-3 model to generate image content.
        fallback (Optional[str]): Fallback prompt to use when the original prompt contains
            human-related items. Defaults to None.
        step (Optional[int]): The number of pixels to shift the square in each direction
            during the iterative inpainting process. Defaults to None.
        square (int): Size of the square region to inpaint in pixels. Defaults to 1024.
        humans (bool): Whether to include human-related items in the prompt.
            Defaults to True.
        verbose (bool): Whether to enable verbose logging. Defaults to False.
        api_key (Optional[str]): OpenAI API key. Defaults to None.

    A class for iterative inpainting using OpenAI's Dall-E 2 and GPT-3 models to generate image content from an input image and prompt.

    Attributes:
        image_path (str): Path to input image file.
        out_path (str): Path to save output image file.
        out_width (int): Desired width of output image.
        out_height (int): Desired height of output image.
        prompt (str): Prompt for GPT-3 model to generate image content.
        fallback (Optional[str]): Fallback prompt to use when the original prompt contains human-related items. Defaults to None.
        step (Optional[int]): The number of pixels to shift the square in each direction during the iterative inpainting process. Defaults to None.
        square (int): Size of the square region to inpaint in pixels. Defaults to 1024.
        humans (bool): Whether to include human-related items in the prompt. Defaults to True.
        verbose (bool): Whether to enable verbose logging. Defaults to False.
        api_key (Optional[str]): OpenAI API key. Defaults to None.
        input_width (int): Width of input image.
        input_height (int): Height of input image.
        image (PIL.Image.Image): Input image as a PIL.Image object.
        out_image (PIL.Image.Image): Output image as a PIL.Image object.
        center_of_focus (Tuple[int,int]): Coordinates of center of focus in input image.
        expansion (Tuple[int,int,int,int]): Expansion values for input image to fit output size.
        human_boxes (List[Tuple[int,int,int,int]]): List of bounding boxes for detected humans in input image.

    Methods:
        configure_logging(): Sets up logging configuration based on verbose flag.
        timestamp(): Returns current timestamp in format '%Y%m%d-%H%M%S'.
        snapshot(): Takes snapshot of current output image and saves to disk.
        open_image(): Opens input image and converts to RGBA format.
        save_image(): Saves output image to disk in PNG format.
        to_rgba(image): Converts input image to RGBA format and returns.
        to_png(image): Converts input image to PNG format and returns binary data.
        make_prompt_fallback(): Generates fallback prompt if given prompt contains human-related items.
        create_out_image(): Creates new RGBA image of size out_width x out_height with transparent background and returns.
        detect_humans(): Detects humans in input image using YOLOv5 model from ultralytics package.
        detect_faces(): Detects a face in input image using dlib face detector.
        find_center_of_focus(): Finds center of focus for output image.
        calculate_expansion(): Calculates amount of expansion needed to fit input image into output image while maintaining center of focus.
        paste_input_image(): Pastes input image onto output image, taking into account calculated expansion.
        openai_inpaint(png, prompt): Calls OpenAI's Image Inpainting API to inpaint given square of output image.
        get_initial_square_position(): Calculates position of initial square to be inpainted.
        human_in_square(square_box): Checks if given square contains human.
        inpaint_square(square_delta): Inpaints given square based on square_delta.
        create_planned_squares(): Generates list of squares to be inpainted in a specific order.
        move_square(square_delta, direction): Moves given square in specified direction by step size.
        init_progress(value): Initializes progress bar with given value.
        tick_progress(): Updates progress bar to indicate completion of one iteration of inpainting process.
        iterative_inpainting(): Performs iterative inpainting process by calling inpaint_square() method on each square in planned square list.
        inpaint(): Main entry point for Multinpainter_OpenAI class. Initializes inpainting
    
    Usage:
        from multinpainter import Multinpainter_OpenAI
        inpainter = Multinpainter_OpenAI(
            image_path="input_image.png",
            out_path="output_image.png",
            out_width=1920,
            out_height=1080,
            prompt="Asian woman in front of blue wall",
            fallback="Solid blue wall",
            square=1024,
            step=256,
            humans=True,
            verbose=True
        )
        inpainter.inpaint()
        print(inpainter.out_path)
    """
    def __init__(
        self,
        image_path: Union[str, Path],
        out_path: Union[str, Path],
        out_width: int,
        out_height: int,
        prompt: str,
        fallback: Optional[str] = None,
        step: Optional[int] = None,
        square: int = 1024,
        humans: bool = True,
        verbose: bool = False,
        api_key: Optional[str] = None,
    ):
        """
        - Initialize the Multinpainter_OpenAI instance with the required input parameters.
        - Set up logging configurations.
        - Open the input image and create an output image.
        - Optionally detect humans in the input image using the YOLO model.
        - Optionally detect faces in the input image using the Dlib library.
        - Find the center of focus of the image (center of input image or the face if found).
        - Calculate the expansion of the output image.
        - Paste the input image onto the output image.
        - Create the outpainting plan by generating a list of square regions in different directions.

        Args:
            image_path (Union[str, Path]): The path of the input image file.
            out_path (Union[str, Path]): The path for the output inpainted image file.
            out_width (int): The width of the output image.
            out_height (int): The height of the output image.
            prompt (str): The prompt text to be used in the inpainting process.
            fallback (Optional[str], optional): The fallback prompt text, used when inpainting non-human areas. Defaults to None.
            step (Optional[int], optional): The step size to move the inpainting square. Defaults to None.
            square (int, optional): The size of the inpainting square. Defaults to 1024.
            humans (bool, optional): Whether to consider humans in the inpainting process. Defaults to True.
            verbose (bool, optional): Whether to show verbose logging. Defaults to False.
            api_key (Optional[str], optional): The OpenAI API key. Defaults to None.
        """
        self.verbose = verbose
        self.configure_logging()
        logging.info("Starting iterative OpenAI inpainter...")
        openai.api_key = api_key or os.environ.get("OPENAI_API_KEY", None)
        if not openai.api_key:
            logging.error(
                "OpenAI API key is missing: must be parameter or 'OPENAI_API_KEY' env variable."
            )
        self.image_path = Path(image_path)
        logging.info(f"Image path: {self.image_path}")
        self.out_path = Path(out_path)
        logging.info(f"Output path: {self.out_path}")
        self.open_image()
        self.out_width = out_width
        self.out_height = out_height
        logging.info(f"Output size: {self.out_width}x{self.out_height}")
        self.square = square
        logging.info(f"Square size: {self.square}")
        self.step = step or square // 2
        logging.info(f"Step size: {self.step}")
        self.out_image = self.create_out_image()
        self.center_of_focus = None
        self.prompt = prompt
        self.prompt_human = prompt
        self.fallback = fallback
        self.prompt_fallback = self.fallback if fallback else self.prompt
        logging.info(f"Human prompt: {self.prompt_human}")
        self.humans = humans
        self.find_center_of_focus()
        self.expansion = self.calculate_expansion()
        self.human_boxes = self.detect_humans() if self.humans else []
        if len(self.human_boxes):
            self.make_prompt_fallback()
        self.paste_input_image()
        self.planned_squares = self.create_planned_squares()
        self.progress = None

    def configure_logging(self) -> None:
        """
        Configures the logging settings for the application.
        """
        log_level = logging.DEBUG if self.verbose else logging.WARNING
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    def timestamp() -> str:
        """
        Returns the current timestamp in the format 'YYYYMMDD-HHMMSS'.

        Returns:
            str: The current timestamp as a string.
        """
        return datetime.now().strftime("%Y%m%d-%H%M%S")

    def snapshot(self) -> None:
        """
        Saves a snapshot of the current output image with a timestamp in the file name. Only saves the snapshot if the verbose flag is set to True.
        """
        if self.verbose:
            snapshot_path = Path(
                self.out_path.parent,
                f"{self.out_path.stem}-{self.timestamp()}.png",
            )
            logging.info(f"Saving snapshot: {snapshot_path}")
            self.out_image.save(
                snapshot_path,
                format="PNG",
            )

    def open_image(self) -> None:
        """
        Opens the input image from the specified image path, converts it to RGBA format, and stores the image and its dimensions as instance variables.
        """
        self.image = self.to_rgba(Image.open(self.image_path))
        self.input_width, self.input_height = self.image.size
        logging.info(f"Input size: {self.input_width}x{self.input_height}")

    def save_image(self) -> None:
        """
        Saves the output image to the specified output path with a PNG format.
        """
        self.out_image.save(self.out_path.with_suffix(".png"), format="PNG")
        logging.info(f"Output image saved to: {self.out_path}")

    def to_rgba(self, image: Image) -> Image:
        """
        Converts the given image to RGBA format and returns the converted image.
        
        Args:
            image (Image): The input image to be converted.

        Returns:
            Image: The converted RGBA image.
        """

        return image.convert("RGBA")

    def to_png(self, image: Image) -> bytes:
        """
        Converts the given image to PNG format and returns the PNG data as bytes.
        
        Args:
            image (Image): The input image to be converted.

        Returns:
            bytes: The PNG data of the converted image.
        """
        png = io.BytesIO()
        image.save(png, format="PNG")
        return png.getvalue()

    def make_prompt_fallback(self):
        """
        Generates a non-human version of the prompt using the GPT-3.5-turbo model.
        The method updates the instance variable `prompt_fallback` with the non-human version of the prompt.
        If a fallback prompt is already provided, this method does nothing.
        """

        if self.fallback:
            return False
        prompt = f"""Create a JSON dictionary. Rewrite this text into one Python list of short phrases, focusing on style, on the background, and on overall scenery, but ignoring humans and human-related items: "{self.prompt_human}". Put that list in the `descriptors` item. In the `ignored` item, put a list of the items from the `descriptors` list that have any relation to humans, human activity or human properties. In the `approved` item, put a list of the items from the `descriptors` list which are not in the `ignore` list, but also include items from the `descriptors` list that relate to style or time. Output only the JSON dictionary, no commentary or explanations."""
        logging.info(f"Adapting to non-human prompt:\n{prompt}")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": ""},
                {"role": "user", "content": prompt},
            ],
        )
        result = response.choices[0].message.content
        logging.info(f"Non-human prompt result: {result}")
        try:
            prompt_fallback = json.loads(result).get("approved", [])
            self.prompt_fallback = ", ".join(prompt_fallback) + ", no humans"
            logging.info(f"Non-human prompt: {self.prompt_fallback}")
        except json.decoder.JSONDecodeError:
            logging.warning(f"Invalid non-human prompt: {result}")

    def create_out_image(self):
        """
        Creates the output image by combining the input image and the generated text.
        The method uses the instance variables `image` and `generated_text` to create the final output image.
        The resulting image is stored in the instance variable `out_image`.
        """
        return Image.new("RGBA", (self.out_width, self.out_height), (0, 0, 0, 0))

    def detect_humans(self):
        """
        Detects human faces or bodies in the input image using a pre-trained model.
        The method processes the instance variable `image` and returns a list of detected human bounding boxes.
        Each bounding box is represented as a tuple (x, y, width, height).

        Returns:
            list: A list of detected human bounding boxes in the input image.
        """
        from ultralytics import YOLO

        boxes = []
        model = YOLO("yolov8n.pt")
        model.classes = [
            0
        ]  # only considering class 'person' and not the 79 other classes...
        model.conf = 0.6  # only considering detection above the threshold.
        detection = model.predict(self.image)
        for box_obj in detection:
            box = box_obj.boxes.xyxy.tolist()[0]
            boxes.append(
                (
                    int(box[0] - 0.5) + self.expansion[0],
                    int(box[1] - 0.5) + self.expansion[1],
                    int(box[2] + 0.5) + self.expansion[0],
                    int(box[3] + 0.5) + self.expansion[1],
                )
            )
        logging.info(f"Detected humans: {boxes}")
        return boxes

    def detect_faces(self):
        """
        Detects human faces in the input image using a pre-trained model.
        The method processes the instance variable `image` and returns a list of detected face bounding boxes.
        Each bounding box is represented as a tuple (x, y, width, height).

        Returns:
            list: A list of detected face bounding boxes in the input image.
        """
        import dlib

        face_detector = dlib.get_frontal_face_detector()
        logging.info("Detecting faces...")
        faces = face_detector(np.array(self.image.convert("RGB")), 1)
        return faces[0] if faces and len(faces) else None

    def find_center_of_focus(self):
        """
        Calculates the center of focus in the input image based on the positions of detected faces and humans.
        The method processes the instance variable `image` and uses the results of `detect_faces` and `detect_humans`
        to determine an optimal focal point for cropping or other image processing tasks.

        Returns:
            tuple: A tuple (x, y) representing the coordinates of the calculated center of focus in the input image.
        """
        face = self.detect_faces() if self.humans else None
        if face:
            logging.info(f"Found face: {face}")
            x_center = (face.left() + face.right()) // 2
            y_center = (face.top() + face.bottom()) // 2
        else:
            x_center = self.input_width // 2
            y_center = self.input_height // 2

        self.center_of_focus = (x_center, y_center)
        logging.info(
            f"Center of focus: {self.center_of_focus[0]}x{self.center_of_focus[1]}"
        )

    def calculate_expansion(self):
        x_percentage = self.center_of_focus[0] / self.input_width
        y_percentage = self.center_of_focus[1] / self.input_height

        x_left = int((self.out_width - self.input_width) * x_percentage)
        x_right = self.out_width - self.input_width - x_left
        y_top = int((self.out_height - self.input_height) * y_percentage)
        y_bottom = self.out_height - self.input_height - y_top

        return x_left, x_right, y_top, y_bottom

    def paste_input_image(self):
        """
        Pastes the input image onto the output image, considering the calculated expansion values.
        This method ensures that the input image is placed onto the output image, taking into account
        the expansion values to position the input image correctly within the output image canvas.
        """
        self.out_image.paste(self.image, (self.expansion[0], self.expansion[2]))

    def openai_inpaint(self, png: bytes, prompt: str) -> Image:
        """
        Generates an inpainted image square using the OpenAI API.

        Args:
            png (bytes): The image data in PNG format, containing the region to be inpainted.
            prompt (str): The text prompt to guide the OpenAI API in inpainting the image.

        Returns:
            PIL.Image.Image: The inpainted image square returned by the OpenAI API.
        """

        response = openai.Image.create_edit(
            image=png,
            mask=png,
            prompt=prompt,
            n=1,
            size=f"{self.square}x{self.square}",
        )
        image_url = response["data"][0]["url"]
        return Image.open(io.BytesIO(requests.get(image_url).content))

    def get_initial_square_position(self):
        """
        Calculates the initial position of the square used for inpainting.

        Returns:
            Tuple[int, int]: The initial (x, y) position of the top-left corner of the square.
        """
        x_init = max(0, self.expansion[0] - (self.square - self.input_width) // 2)
        y_init = max(0, self.expansion[2] - (self.square - self.input_height) // 2)
        return x_init, y_init

    def human_in_square(self, square_box: Tuple[int, int, int, int]) -> bool:
        """
        Determines whether any detected human bounding boxes intersect with the given square_box.

        Args:
            square_box (Tuple[int, int, int, int]): The (x0, y0, x1, y1) coordinates of the square_box.

        Returns:
            bool: True if any detected human bounding boxes intersect with the square_box, False otherwise.
        """
        x0, y0, x1, y1 = square_box

        for box in self.human_boxes:
            bx0, by0, bx1, by1 = box
            if x0 < bx1 and x1 > bx0 and y0 < by1 and y1 > by0:
                return True
        return False

    def inpaint_square(self, square_delta: Tuple[int, int]) -> None:
        """
        Inpaints the square region in the output image specified by square_delta using OpenAI's API.
        Chooses the appropriate prompt based on the presence of humans in the square.

        Args:
            square_delta (Tuple[int, int]): The (x, y) coordinates of the top-left corner of the square region.

        Returns:
            None
        """
        x, y = square_delta
        x1, y1 = x + self.square, y + self.square
        # Check if the square is fully enclosed inside the pasted input image
        if (
            x >= self.expansion[0]
            and y >= self.expansion[2]
            and x1 <= (self.expansion[0] + self.input_width)
            and y1 <= (self.expansion[2] + self.input_height)
        ):
            return
        square = self.out_image.crop((x, y, x1, y1))
        png = self.to_png(square)

        if self.human_in_square((x, y, x1, y1)):
            prompt = self.prompt_human
        else:
            prompt = self.prompt_fallback

        logging.info(f"Inpainting region {x} {y} {x1} {y1} with: {prompt}")
        inpainted_square = self.openai_inpaint(png, prompt)
        self.out_image.paste(inpainted_square, (x, y))
        self.snapshot()

    def create_planned_squares(self):
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

        init_square = self.get_initial_square_position()

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
                cur_x, cur_y = self.move_square((cur_x, cur_y), direction)
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
        self, square_delta: Tuple[int, int], direction: str
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
            next_y = max(0, y - self.step)
            if next_y == y:
                return x, None
            return x, next_y
        elif direction == "left":
            next_x = max(0, x - self.step)
            if next_x == x:
                return None, y
            return next_x, y
        elif direction == "right":
            next_x = min(x + self.step, self.out_width - self.square)
            if next_x == x:
                return None, y
            return next_x, y
        elif direction == "down":
            next_y = min(y + self.step, self.out_height - self.square)
            if next_y == y:
                return x, None
            return x, next_y

    def init_progress(self, value: int):
        """
        Initializes a progress bar for the iterative inpainting process.

        Args:
        - value: An integer representing the total number of iterations that the progress bar will track.
        """

        self.progress = Bar("Outpainting square", max=value)

    def tick_progress(self):
        """
        Advances the progress bar by one tick.
        """
        if self.verbose:
            print()
        self.progress.next()
        if self.verbose:
            print()

    def iterative_inpainting(self):
        """
        Iteratively performs the inpainting process by calling `inpaint_square` on each square in the order defined by `create_planned_squares`.
        Initializes and updates a progress bar to track the progress of the inpainting process.
        """

        inpainting_plan = []
        for direction in self.planned_squares:
            inpainting_plan += self.planned_squares[direction]
        self.init_progress(len(inpainting_plan))

        for square_delta in inpainting_plan:
            self.tick_progress()
            self.inpaint_square(square_delta)

    def inpaint(self):
        """
        - Perform outpainting for each square in the outpainting plan.
        - Save the output image.
        """

        self.iterative_inpainting()
        self.save_image()
