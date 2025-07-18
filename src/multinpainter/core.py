import logging
import os
from pathlib import Path

import openai
from PIL import Image
from tqdm import tqdm

from . import image_utils
from . import prompt_utils
from . import detection_utils
from . import inpainting_core
from .models import describe_image_hf, detect_humans_yolo, detect_faces_dlib, inpaint_square_openai

__author__ = "Adam Twardoch"
__license__ = "Apache-2.0"

DESCRPTION_MODEL = "Salesforce/blip2-opt-2.7b"


class Multinpainter_OpenAI:
    f"""
    A class for iterative inpainting using OpenAI's Dall-E 2 and GPT-3 artificial intelligence models to extend (outpaint) an existing image to new defined dimensions.

    This class orchestrates the entire outpainting process by delegating specific tasks to specialized utility modules.

    Args:
        image_path (str): Path to the input image file.
        out_path (str): Path to save the output image file.
        out_width (int): Desired width of the output image.
        out_height (int): Desired height of the output image.
        prompt (str, optional): Prompt for the GPT-3 model to generate image content.
        fallback (str, optional): Fallback prompt to use when the original prompt contains
            human-related items. Defaults to None.
        step (int, optional): The number of pixels to shift the square in each direction
            during the iterative inpainting process. Defaults to None.
        square (int, optional): Size of the square region to inpaint in pixels. Defaults to 1024.
        humans (bool, optional): Whether to include human-related items in the prompt.
            Defaults to True.
        verbose (bool, optional): Whether to enable verbose logging. Defaults to False.
        openai_api_key (str, optional): OpenAI API key or OPENAI_API_KEY env variable.
        hf_api_key (str, optional): Huggingface API key or HUGGINGFACEHUB_API_TOKEN env variable.
        prompt_model (str, optional): The Huggingface model to describe image. Defaults to "{DESCRPTION_MODEL}".

    Attributes:
        image_path (Path): Path to input image file.
        out_path (Path): Path to save output image file.
        out_width (int): Desired width of output image.
        out_height (int): Desired height of output image.
        prompt (str): Prompt for GPT-3 model to generate image content.
        fallback (str): Fallback prompt to use when the original prompt contains human-related items. Defaults to None.
        step (int): The number of pixels to shift the square in each direction during the iterative inpainting process. Defaults to None.
        square (int): Size of the square region to inpaint in pixels. Defaults to 1024.
        humans (bool): Whether to include human-related items in the prompt. Defaults to True.
        verbose (bool): Whether to enable verbose logging. Defaults to False.
        openai_api_key (str): OpenAI API key or OPENAI_API_KEY env variable.
        hf_api_key (str): Huggingface API key or HUGGINGFACEHUB_API_TOKEN env variable.
        prompt_model (str): Huggingface model to describe image. Defaults to "{DESCRPTION_MODEL}".
        input_width (int): Width of input image.
        input_height (int): Height of input image.
        image (PIL.Image.Image): Input image as a PIL.Image object.
        out_image (PIL.Image.Image): Output image as a PIL.Image object.
        center_of_focus (Tuple[int,int]): Coordinates of center of focus in input image.
        expansion (Tuple[int,int,int,int]): Expansion values for input image to fit output size.
        human_boxes (List[Tuple[int,int,int,int]]): List of bounding boxes for detected humans in input image.

    Methods:
        configure_logging(): Sets up logging configuration based on verbose flag.
        create_out_image(): Creates new RGBA image of size out_width x out_height with transparent background.
        describe_image(): Generates prompt using a Huggingface image captioning model.
        detect_humans(): Detects humans in input image using YOLOv5 model.
        detect_faces(): Detects a face in input image using dlib face detector.
        find_center_of_focus(): Finds center of focus for output image.
        inpaint_square(square_delta): Inpaints given square based on square_delta.
        iterative_inpainting(): Performs iterative inpainting process.
        inpaint(): Asynchronous main entry point for Multinpainter_OpenAI class.

    Usage:
        import asyncio
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
            verbose=True,
            openai_api_key="sk-NNNNNN",
            hf_api_key="hf_NNNNNN",
            prompt_model="{DESCRPTION_MODEL}"
        )
        asyncio.run(inpainter.inpaint())
    """

    def __init__(
        self,
        image_path: str | Path,
        out_path: str | Path = None,
        out_width: int = 0,
        out_height: int = 0,
        prompt: str | None = None,
        fallback: str | None = None,
        step: int | None = None,
        square: int = 1024,
        humans: bool = True,
        verbose: bool = False,
        openai_api_key: str | None = None,
        hf_api_key: str | None = None,
        prompt_model: str = None,
    ):
        f"""
        Initializes the Multinpainter_OpenAI instance.

        Args:
            image_path (Union[str, Path]): The path of the input image file.
            out_path (Union[str, Path]): The path for the output inpainted image file.
            out_width (int): The width of the output image.
            out_height (int): The height of the output image.
            prompt (str, optional): The prompt text to be used in the inpainting process.
            fallback (str, optional): The fallback prompt text, used when inpainting non-human areas. Defaults to None.
            step (int, optional): The step size to move the inpainting square. Defaults to None.
            square (int, optional): The size of the inpainting square. Defaults to 1024.
            humans (bool, optional): Whether to consider humans in the inpainting process. Defaults to True.
            verbose (bool, optional): Whether to show verbose logging. Defaults to False.
            openai_api_key (str, optional): Your OpenAI API key, defaults to the OPENAI_API_KEY environment variable.
            hf_api_key (str, optional): Your Huggingface API key, defaults to the HUGGINGFACEHUB_API_TOKEN env variable.
            prompt_model (str, optional): The Huggingface model to describe image. Defaults to "{DESCRPTION_MODEL}".
        """
        self.verbose = verbose
        self.configure_logging()
        logging.info("Starting iterative OpenAI inpainter...")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY", None)
        openai.openai_api_key = self.openai_api_key
        self.hf_api_key = hf_api_key or os.environ.get("HUGGINGFACEHUB_API_TOKEN", None)
        self.image_path = Path(image_path)
        logging.info(f"Image path: {self.image_path}")
        self.image, self.input_width, self.input_height = image_utils.open_image(self.image_path)
        self.out_width = out_width
        self.out_height = out_height
        if not out_path:
            out_path = self.image_path.with_name(
                f"{self.image_path.stem}_outpainted-{self.out_width}x{self.out_height}.png"
            )
        self.out_path = Path(out_path)
        logging.info(f"Output path: {self.out_path}")
        logging.info(f"Output size: {self.out_width}x{self.out_height}")
        self.prompt = prompt
        self.fallback = fallback
        self.prompt_model = (
            prompt_model or DESCRPTION_MODEL
        )  # "Salesforce/blip2-opt-6.7b-coco" #
        self.square = square
        self.step = step or square // 2
        self.center_of_focus = None
        self.humans = humans
        self.face_boxes = None

    def prep_inpainting(self):
        logging.info(f"Square size: {self.square}")
        logging.info(f"Step size: {self.step}")
        self.out_image = self.create_out_image()
        self.detect_faces()
        self.find_center_of_focus()
        self.expansion = inpainting_core.calculate_expansion(self.center_of_focus, self.input_width, self.input_height, self.out_width, self.out_height)
        self.human_boxes = self.detect_humans() if self.humans else []
        if len(self.human_boxes):
            self.prompt_fallback = prompt_utils.make_prompt_fallback(self.prompt_human, self.fallback)
        inpainting_core.paste_input_image(self.out_image, self.image, self.expansion)
        self.planned_squares = inpainting_core.create_planned_squares(inpainting_core.get_initial_square_position(self.expansion, self.square, self.input_width, self.input_height), self.square, self.step, self.out_width, self.out_height)

    def configure_logging(self) -> None:
        """
        Configures the logging settings for the application.
        """
        log_level = logging.DEBUG if self.verbose else logging.WARNING
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    

    

    def create_out_image(self):
        """
        Creates a new RGBA image of the specified output dimensions with a transparent background.

        Returns:
            PIL.Image.Image: The newly created blank RGBA image.
        """
        return Image.new("RGBA", (self.out_width, self.out_height), (0, 0, 0, 0))

    async def describe_image(self):
        """
        Generates a prompt for the image using a Huggingface image captioning model.
        The generated prompt is stored in the `self.prompt` attribute.
        """
        logging.info("Describing image...")
        self.prompt = await describe_image_hf(
            self.image, self.prompt_model, self.hf_api_key
        )

    def detect_humans(self):
        """
        Detects human faces or bodies in the input image using the YOLOv8 model.
        The detected human bounding boxes are stored in `self.human_boxes`.
        """
        self.human_boxes = detect_humans_yolo(self.image)
        logging.info(f"Detected humans: {self.human_boxes}")

    def detect_faces(self):
        self.face_boxes = detect_faces_dlib(self.image)
        logging.info(f"Detected faces: {self.face_boxes}")

    def find_center_of_focus(self):
        """
        Calculates the center of focus in the input image based on the positions of detected faces and humans.
        The method processes the instance variable `image` and uses the results of `detect_faces` and `detect_humans`
        to determine an optimal focal point for cropping or other image processing tasks.

        Returns:
            tuple: A tuple (x, y) representing the coordinates of the calculated center of focus in the input image.
        """
        if self.face_boxes:
            x_min, y_min, x_max, y_max = self.face_boxes[0]
            center_x = (x_min + x_max) // 2
            center_y = (y_min + y_max) // 2
            self.center_of_focus = center_x, center_y
        else:
            self.center_of_focus = self.image.size[0] // 2, self.image.size[1] // 2
        logging.info(f"Center of focus: {self.center_of_focus}")

    

    async def iterative_inpainting(self):
        """
        Iteratively performs the inpainting process by calling `inpaint_square` on each square in the order defined by `create_planned_squares`.
        Initializes and updates a progress bar to track the progress of the inpainting process.
        """
        if not self.prompt:
            self.prompt = await self.describe_image()
        self.prompt_human = self.prompt
        logging.info(f"Human prompt: {self.prompt_human}")
        self.prompt_fallback = self.fallback or self.prompt
        logging.info(f"Fallback prompt: {self.prompt_fallback}")

        inpainting_plan = [
            square_delta
            for direction in self.planned_squares
            for square_delta in self.planned_squares[direction]
        ]
        progress_bar = tqdm(
            inpainting_plan, desc="Outpainting square", total=len(inpainting_plan)
        )
        for square_delta in progress_bar:
            await self.inpaint_square(square_delta)

    async def inpaint(self):
        """
        - Asynchronously perform outpainting for each square in the outpainting plan.
        - Save the output image.
        """
        self.prep_inpainting()
        await self.iterative_inpainting()
        image_utils.save_image(self.out_image, self.out_path)
