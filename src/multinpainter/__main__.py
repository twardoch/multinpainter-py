#!/usr/bin/env python3

import fire
from multinpainter import __version__
from .multinpainter import Multinpainter_OpenAI, read_prompt

def inpaint(
    image,
    output,
    width,
    height,
    prompt=None,
    fallback=None,
    step=None,
    square=1024,
    humans=False,
    verbose=False,
    api_key=None,
):
    if not prompt:
        prompt = read_prompt(image)

    inpainter = Multinpainter_OpenAI(
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
        api_key=api_key,
    )
    inpainter.inpaint()
    return inpainter.out_path

def cli():
    fire.core.Display = lambda lines, out: print(*lines, file=out)
    fire.Fire(inpaint, name="multinpainter-py")
    
if __name__ == "__main__":
    cli()
    