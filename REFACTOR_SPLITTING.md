# Code Refactoring Plan: Splitting `multinpainter.py`

This plan outlines the steps to split the large `multinpainter.py` file into smaller, more focused modules. The goal is to improve code organization, maintainability, and readability without altering the existing functionality.

## Current State Analysis

The `src/multinpainter/multinpainter.py` file currently contains a single large class, `Multinpainter_OpenAI`, which encapsulates a wide range of responsibilities including:
- Initialization and configuration management.
- Image loading, saving, and manipulation.
- Prompt generation and fallback logic.
- Human and face detection.
- Core inpainting algorithm and related calculations.
- Orchestration of the entire outpainting process.

While some external functions are already used from `src/multinpainter/models.py` (e.g., `describe_image_hf`, `detect_humans_yolo`, `detect_faces_dlib`, `inpaint_square_openai`), the `Multinpainter_OpenAI` class itself remains monolithic.

## Proposed Modularization

The `Multinpainter_OpenAI` class will be refactored to act primarily as an orchestrator, delegating specific tasks to newly created, specialized modules.

The following new modules will be created within the `src/multinpainter/` directory:

1.  **`image_utils.py`**: For all image-related utility functions.
2.  **`prompt_utils.py`**: For functions related to prompt generation and manipulation.
3.  **`detection_utils.py`**: For functions related to human and face detection logic (excluding the actual model calls which remain in `models.py`).
4.  **`inpainting_core.py`**: For the core inpainting algorithm logic and related calculations.
5.  **`core.py`**: This will be the new name for the main `Multinpainter_OpenAI` class file, serving as the central coordinating component.

## Detailed Refactoring Steps

A junior software developer should follow these steps sequentially, verifying changes after each major step.

### Step 1: Create New Files and Move Functions

**1.1. Create `src/multinpainter/image_utils.py`**

*   Create a new file: `src/multinpainter/image_utils.py`.
*   Move the following functions from `src/multinpainter/multinpainter.py` to `src/multinpainter/image_utils.py`:
    *   `to_rgba(image: Image) -> Image`
    *   `timestamp() -> str`
    *   `snapshot(image: Image, out_path: Path, timestamp_func: Callable, verbose: bool) -> None`
        *   **Modification**: This function will no longer be a method. It needs to accept `image`, `out_path`, a `timestamp_func` (e.g., `image_utils.timestamp`), and `verbose` as arguments.
    *   `open_image(image_path: Path) -> Tuple[Image, int, int]`
        *   **Modification**: This function will no longer be a method. It needs to accept `image_path` and return the `Image` object, `input_width`, and `input_height`. It will also need to import `Image` and `Path`.
    *   `save_image(image: Image, out_path: Path) -> None`
        *   **Modification**: This function will no longer be a method. It needs to accept `image` and `out_path`. It will also need to import `Path`.
*   Add necessary imports to `image_utils.py`: `from PIL import Image`, `from pathlib import Path`, `from datetime import datetime`, `import logging`, `from typing import Callable, Tuple`.

**1.2. Create `src/multinpainter/prompt_utils.py`**

*   Create a new file: `src/multinpainter/prompt_utils.py`.
*   Move the `make_prompt_fallback` function from `src/multinpainter/multinpainter.py` to `src/multinpainter/prompt_utils.py`.
*   **Modification**: This function will no longer be a method. It needs to accept `prompt_human: str` and `fallback: str | None` as arguments. It should return the generated `prompt_fallback` string.
*   Add necessary imports to `prompt_utils.py`: `import json`, `import logging`, `import openai`.

**1.3. Create `src/multinpainter/detection_utils.py`**

*   Create a new file: `src/multinpainter/detection_utils.py`.
*   Move the `human_in_square` function from `src/multinpainter/multinpainter.py` to `src/multinpainter/detection_utils.py`.
*   **Modification**: This function will no longer be a method. It needs to accept `square_box: tuple[int, int, int, int]` and `human_boxes: list[tuple[int, int, int, int]]` as arguments.
*   No additional imports are immediately necessary for this specific function.

**1.4. Create `src/multinpainter/inpainting_core.py`**

*   Create a new file: `src/multinpainter/inpainting_core.py`.
*   Move the following functions from `src/multinpainter/multinpainter.py` to `src/multinpainter/inpainting_core.py`:
    *   `calculate_expansion(center_of_focus: tuple[int, int], input_width: int, input_height: int, out_width: int, out_height: int) -> tuple[int, int, int, int]`
        *   **Modification**: This function will no longer be a method. It needs to accept all its required parameters as arguments.
    *   `paste_input_image(out_image: Image, input_image: Image, expansion: tuple[int, int, int, int]) -> None`
        *   **Modification**: This function will no longer be a method. It needs to accept `out_image`, `input_image`, and `expansion` as arguments. It will need to import `Image`.
    *   `get_initial_square_position(expansion: tuple[int, int, int, int], square: int, input_width: int, input_height: int) -> tuple[int, int]`
        *   **Modification**: This function will no longer be a method. It needs to accept `expansion`, `square`, `input_width`, and `input_height` as arguments.
    *   `create_planned_squares(initial_square_position: tuple[int, int], square_size: int, step_size: int, out_width: int, out_height: int) -> OrderedDict`
        *   **Modification**: This function will no longer be a method. It needs to accept `initial_square_position`, `square_size`, `step_size`, `out_width`, and `out_height` as arguments. It will need to import `OrderedDict`, `logging`.
    *   `move_square(square_delta: tuple[int, int], direction: str, step: int, out_width: int, out_height: int, square: int) -> tuple[int, int]`
        *   **Modification**: This function will no longer be a method. It needs to accept all its required parameters as arguments.
*   Add necessary imports to `inpainting_core.py`: `from collections import OrderedDict`, `import logging`, `from PIL import Image`, `from typing import Tuple`.

### Step 2: Update `Multinpainter_OpenAI` Class (in `src/multinpainter/multinpainter.py`)

*   **Remove Moved Functions**: Delete the implementations of `timestamp`, `snapshot`, `open_image`, `save_image`, `to_rgba`, `make_prompt_fallback`, `human_in_square`, `calculate_expansion`, `paste_input_image`, `get_initial_square_position`, `create_planned_squares`, and `move_square` from the `Multinpainter_OpenAI` class.
*   **Update `__init__` Method**:
    *   The `self.image` and `self.input_width`, `self.input_height` attributes should be set by calling `image_utils.open_image`.
    *   The `self.timestamp` attribute should be set to `image_utils.timestamp`.
*   **Update Method Calls**:
    *   `self.configure_logging()` remains as is.
    *   `self.open_image()` should be replaced with `self.image, self.input_width, self.input_height = image_utils.open_image(self.image_path)`.
    *   `self.save_image()` should be replaced with `image_utils.save_image(self.out_image, self.out_path)`.
    *   `self.snapshot()` should be replaced with `image_utils.snapshot(self.out_image, self.out_path, self.timestamp, self.verbose)`.
    *   `self.to_rgba()` calls should be replaced with direct calls to `image_utils.to_rgba`.
    *   `self.make_prompt_fallback()` should be replaced with `self.prompt_fallback = prompt_utils.make_prompt_fallback(self.prompt_human, self.fallback)`.
    *   `self.calculate_expansion()` should be replaced with `self.expansion = inpainting_core.calculate_expansion(self.center_of_focus, self.input_width, self.input_height, self.out_width, self.out_height)`.
    *   `self.paste_input_image()` should be replaced with `inpainting_core.paste_input_image(self.out_image, self.image, self.expansion)`.
    *   `self.get_initial_square_position()` should be replaced with `initial_pos = inpainting_core.get_initial_square_position(self.expansion, self.square, self.input_width, self.input_height)`.
    *   `self.human_in_square()` should be replaced with `detection_utils.human_in_square(square_box, self.human_boxes)`.
    *   `self.create_planned_squares()` should be replaced with `self.planned_squares = inpainting_core.create_planned_squares(initial_pos, self.square, self.step, self.out_width, self.out_height)`.
    *   `self.move_square()` should be replaced with `inpainting_core.move_square(square_delta, direction, self.step, self.out_width, self.out_height, self.square)`.
    *   The `func_describe`, `func_detect`, `func_inpaint` parameters in `describe_image`, `detect_humans`, `detect_faces`, and `inpaint_square` methods should be removed. Instead, directly import and call the functions from `models.py`.
*   **Add Imports**: Add the following imports to `src/multinpainter/multinpainter.py`:
    ```python
    from . import image_utils
    from . import prompt_utils
    from . import detection_utils
    from . import inpainting_core
    from .models import describe_image_hf, detect_humans_yolo, detect_faces_dlib, inpaint_square_openai
    ```
*   **Update Docstrings**: Adjust the docstrings of the `Multinpainter_OpenAI` class and its methods to reflect the new responsibilities and the delegation to other modules.

### Step 3: Refactor `models.py` (Minor Changes)

*   **Verify `detect_humans_yolo`**: Ensure that the `detect_humans` method in `Multinpainter_OpenAI` (or `core.py` later) correctly calls `detect_humans_yolo` from `models.py` as per the `TODO.md` list. The current code already uses `detect_humans_yolov8` which should be `detect_humans_yolo`. This will be a direct change in `multinpainter.py` (or `core.py`).

### Step 4: Update `__init__.py` and `__main__.py`

*   **`src/multinpainter/__init__.py`**:
    *   Update the import statement: `from .multinpainter import DESCRPTION_MODEL, Multinpainter_OpenAI` should become `from .core import DESCRPTION_MODEL, Multinpainter_OpenAI` (after renaming in Step 5).
*   **`src/multinpainter/__main__.py`**:
    *   Update the import statement: `from .multinpainter import Multinpainter_OpenAI` should become `from .core import Multinpainter_OpenAI` (after renaming in Step 5).

### Step 5: Rename `multinpainter.py` to `core.py`

*   Once all the above refactoring steps are completed and verified, rename the file `src/multinpainter/multinpainter.py` to `src/multinpainter/core.py`.
*   Ensure all references to `multinpainter.multinpainter` in other files (e.g., `__init__.py`, `__main__.py`) are updated to `multinpainter.core`.

### Step 6: Testing and Verification

*   **Run Existing Tests**: Execute the project's existing test suite (`pytest`) to ensure that no regressions have been introduced by the refactoring.
*   **New Unit Tests**: Write new unit tests specifically for the functions within `image_utils.py`, `prompt_utils.py`, `detection_utils.py`, and `inpainting_core.py`. Mock external dependencies (like OpenAI API calls or Huggingface API calls) where necessary.
*   **Integration Tests**: Perform end-to-end integration tests to verify that the entire outpainting process works correctly with the new modular structure.

### Step 7: Documentation Update

*   **Docstrings**: Review and update all docstrings in the refactored files (`image_utils.py`, `prompt_utils.py`, `detection_utils.py`, `inpainting_core.py`, and `core.py`) to accurately describe their new responsibilities and parameters.
*   **`README.md`**: Update any sections in `README.md` that describe the internal structure or code organization, if applicable.
*   **`PLAN.md`**: Update `PLAN.md` to reflect the completion of this refactoring task.
*   **`CHANGELOG.md`**: Add an entry to `CHANGELOG.md` detailing the refactoring.
*   **`TODO.md`**: Mark relevant tasks as completed in `TODO.md`.

This systematic approach will ensure a smooth and safe refactoring process, resulting in a more modular and maintainable codebase.
