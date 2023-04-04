import io
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from collections import OrderedDict
from typing import Optional, Union

import numpy as np
import openai
import requests
from PIL import Image
from progress.bar import Bar

from multinpainter import __version__

__author__ = "Adam Twardoch"
__license__ = "Apache-2.0"



def read_prompt(png_path: Union[str, Path]) -> Optional[str]:
    with open(f"{Path(png_path).stem}.json") as f:
        prompt = json.load(f)["prompt"]
    logging.info(f"""read_prompt: {prompt}""")
    return prompt


class Multinpainter_OpenAI:
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
        if not step:
            step = int(square / 2)
        self.step = step
        logging.info(f"Step size: {self.step}")
        self.out_image = self.create_out_image()
        self.center_of_focus = None
        self.prompt = prompt
        self.prompt_human = prompt
        self.fallback = fallback
        if fallback:
            self.prompt_fallback = self.fallback
        else:
            self.prompt_fallback = self.prompt
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

    def configure_logging(self):
        log_level = logging.DEBUG if self.verbose else logging.WARNING
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    def timestamp(self):
        return datetime.now().strftime("%Y%m%d-%H%M%S")

    def snapshot(self):
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

    def open_image(self):
        self.image = self.to_rgba(Image.open(self.image_path))
        self.input_width, self.input_height = self.image.size
        logging.info(f"Input size: {self.input_width}x{self.input_height}")

    def save_image(self):
        self.out_image.save(self.out_path.with_suffix(".png"), format="PNG")
        logging.info(f"Output image saved to: {self.out_path}")

    def to_rgba(self, image: Image) -> Image:
        return image.convert("RGBA")

    def to_png(self, image: Image) -> bytes:
        png = io.BytesIO()
        image.save(png, format="PNG")
        return png.getvalue()

    def make_prompt_fallback(self):
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
        return Image.new("RGBA", (self.out_width, self.out_height), (0, 0, 0, 0))

    def detect_humans(self):
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
        import dlib

        face_detector = dlib.get_frontal_face_detector()
        logging.info("Detecting faces...")
        faces = face_detector(np.array(self.image.convert("RGB")), 1)
        return faces[0] if faces and len(faces) else None

    def find_center_of_focus(self):
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
        self.out_image.paste(self.image, (self.expansion[0], self.expansion[2]))

    def openai_inpaint(self, png: str, prompt: str) -> Image:
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
        x_init = max(0, self.expansion[0] - (self.square - self.input_width) // 2)
        y_init = max(0, self.expansion[2] - (self.square - self.input_height) // 2)
        return x_init, y_init

    def human_in_square(self, square_box: Tuple[int, int, int, int]) -> bool:
        x0, y0, x1, y1 = square_box

        for box in self.human_boxes:
            bx0, by0, bx1, by1 = box
            if x0 < bx1 and x1 > bx0 and y0 < by1 and y1 > by0:
                return True
        return False

    def inpaint_square(self, square_delta: Tuple[int, int]) -> None:
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

    def move_square(self, square_delta: Tuple[int, int], direction: str) -> Tuple[int, int]:
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
        self.progress = Bar("Outpainting square", max=value)
    def tick_progress(self):
        if self.verbose:
            print()
        self.progress.next()
        if self.verbose:
            print()

    def iterative_inpainting(self):
        inpainting_plan = []
        for direction in self.planned_squares:
            inpainting_plan += self.planned_squares[direction]
        self.init_progress(len(inpainting_plan))

        for square_delta in inpainting_plan:
            self.tick_progress()
            self.inpaint_square(square_delta)

    def inpaint(self):
        self.iterative_inpainting()
        self.save_image()
