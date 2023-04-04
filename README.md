# Multinpainter

Iterative image outpainting powered by OpenAI Dall-E API.

## Introduction

Multinpainter is a Python library and a CLI tool that can iteratively outpaint an input image using OpenAI’s API. 

You can specify an input image, the size of the output image, and a prompt. Multinpainter will then iteratively call the OpenAI API to outpaint the image step-by-step until the entire output image is filled with content. 

## Installation

```
python3 -m pip install --upgrade git+https://github.com/twardoch/multinpainter-py
```

## Usage

Command-line:

```
NAME
    multinpainter-py

SYNOPSIS
    multinpainter-py IMAGE OUTPUT WIDTH HEIGHT <flags>

POSITIONAL ARGUMENTS
    IMAGE
    OUTPUT
    WIDTH
    HEIGHT

FLAGS
    -p, --prompt=PROMPT
        Type: Optional[]
        Default: None
    -f, --fallback=FALLBACK
        Type: Optional[]
        Default: None
    --step=STEP
        Default: 512
    --square=SQUARE
        Default: 1024
    -h, --humans=HUMANS
        Default: False
    -v, --verbose=VERBOSE
        Default: False
    -a, --api_key=API_KEY
        Type: Optional[]
        Default: None

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

See below for explanation of the arguments. You can also use `python3 -m multinpainter` instead of `multinpainter-py`. 

In Python, you can also do: 

```python
from multinpainter import Multinpainter_OpenAI
inpainter = Multinpainter_OpenAI(
    image_path="input_image.png",
    out_path="output_image.png",
    out_width=1920,
    out_height=1080,
    prompt="Asian woman in front of blue wall",
    fallback="Solid blue wall",
    step=256,
    square=1024,
    humans=True,
    verbose=True,
    api_key="sk-NNNNNNNNNNN",
)
inpainter.inpaint()
print(inpainter.out_path)
```

Here’s an explanation of the arguments: 

| CLI               | Python        | Explanation                                                                                                        |
| ----------------- | ------------- | ------------------------------------------------------------------------------------------------------------------ |
| `IMAGE`           | `image_path` | The path of the input image to be outpainted.                                                                      |
| `OUTPUT`          | `out_path`   | The path where the output image will be saved.                                                                     |
| `WIDTH`           | `out_width`  | The desired width of the output image.                                                                             |
| `HEIGHT`          | `out_height` | The desired height of the output image.                                                                            |
| `-p PROMPT`       | `prompt`      | The main prompt that will guide the outpainting process.                                                           |
| `-f FALLBACK`     | `fallback`    | A fallback prompt used for outpainting when no humans are detected in the image.                                   |
| `--step=STEP`     | `step`        | The step size used to move the outpainting square during the iterative outpainting process.                        |
| `--square=SQUARE` | `square`      | The size of the square region that will be outpainted during each step , must be `1024` or `512` or `256`.         |
| `--humans`        | `humans`      | A boolean flag indicating whether to detect humans in the image and adapt the prompt accordingly.                  |
| `--verbose`       | `verbose`     | If given, prints verbose output and saves intermediate outpainting images.                                         |
| `-a API_KEY`      | `api_key`    | The API key for OpenAI. If not provided, the code will attempt to get it from the `OPENAI_API_KEY` env variable. |

The `inpaint()` method of the class does the following:

- Initialize the class with the required input parameters.
- Set up logging configurations.
- Open the input image and create an output image.
- Optionally detect humans in the input image using the YOLO model.
- Optionally detect faces in the input image using the Dlib library.
- Find the center of focus of the image (center of input image or the face if found).
- Calculate the expansion of the output image.
- Paste the input image onto the output image.
- Create the outpainting plan by generating a list of square regions in different directions.
- Perform outpainting for each square in the outpainting plan.
- Save the output image.

## Note

This project has been set up using PyScaffold 4.4. For details and usage
information on PyScaffold see https://pyscaffold.org/.
