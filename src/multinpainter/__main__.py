#!/usr/bin/env python3

import asyncio

import fire

from .core import Multinpainter_OpenAI


def get_inpainter(*args, **kwargs) -> Multinpainter_OpenAI:
    return Multinpainter_OpenAI(*args, **kwargs)


def inpaint(
    image: str,
    output: str,
    width: int,
    height: int,
    prompt: str | None = None,
    fallback: str | None = None,
    step: int | None = None,
    square: int = 1024,
    humans: bool = False,
    verbose: bool = False,
    openai_api_key: str | None = None,
    hf_api_key: str | None = None,
    prompt_model: str = None,
    *args,
    **kwargs,
) -> str:
    """
    Perform iterative inpainting on an image file using OpenAI's DALL-E 2 model.

    Args:
        image (str): Path to the input image file.
        output (str): Path to the output image file.
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.
        prompt (str, optional): A prompt to guide the image generation.
        fallback (str, optional): A fallback prompt to use if no human is found in the image. If not provided but `humans` is specified, the tool will autogenerate the fallback prompt based on the main prompt.
        step (int, optional): The step size in pixels to move the window during the inpainting process. If not provided, the window will move by half the square size. Defaults to None.
        square (int, optional): The size of the square window to use for inpainting. Must be 1024 (default) or 512 or 256.
        humans (bool, optional): If specified, the algorithm will detect humans and apply the main prompt for squares with a human, and the fallback prompt for squares without a human.
        verbose (bool, optional): If specified, prints verbose info.
        openai_api_key (str, optional): Your OpenAI API key, defaults to the OPENAI_API_KEY environment variable.
        hf_api_key (str, optional): Your Huggingface API key, defaults to the HUGGINGFACEHUB_API_TOKEN env variable.
        prompt_model (str, optional): The Huggingface model to describe image. Defaults to "Salesforce/blip2-opt-2.7b".
    Returns:
        str: The path to the output image file.
    """

    inpainter = get_inpainter(
        image_path=image,
        out_path=output,
        out_width=width,
        out_height=height,
        prompt=prompt,
        fallback=fallback,
        step=step,
        square=square,
        humans=humans,
        verbose=verbose,
        openai_api_key=openai_api_key,
        hf_api_key=hf_api_key,
        prompt_model=prompt_model,
    )
    asyncio.run(inpainter.inpaint())
    return inpainter.out_path


def describe(
    image: str,
    hf_api_key: str | None = None,
    prompt_model: str = None,
    *args,
    **kwargs,
) -> str:
    """
    Describe the image.

    Args:
        image (str): Path to the input image file.
        hf_api_key (str, optional): Your Huggingface API key, defaults to the HUGGINGFACEHUB_API_TOKEN env variable.
        prompt_model (str, optional): The Huggingface model to describe image. Defaults to "Salesforce/blip2-opt-2.7b".
    Returns:
        str: The path to the output image file.
    """

    inpainter = get_inpainter(
        image_path=image,
        hf_api_key=hf_api_key,
        prompt_model=prompt_model,
    )
    asyncio.run(inpainter.describe_image())
    return inpainter.prompt


def cli():
    fire.core.Display = lambda lines, out: print(*lines, file=out)
    fire.Fire(
        {
            "inpaint": inpaint,
            "describe": describe,
        },
        name="multinpainter-py",
    )


if __name__ == "__main__":
    cli()
