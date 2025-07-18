import json
import logging
import openai

def make_prompt_fallback(prompt_human: str, fallback: str | None) -> str:
    """
    Generates a non-human version of the prompt using the GPT-3.5-turbo model.
    If a fallback prompt is already provided, this method does nothing.

    Args:
        prompt_human (str): The original prompt containing human-related items.
        fallback (str | None): An optional pre-defined fallback prompt.

    Returns:
        str: The generated fallback prompt string.
    """
    if fallback:
        return fallback
    prompt = f"""Create a JSON dictionary. Rewrite this text into one Python list of short phrases, focusing on style, on the background, and on overall scenery, but ignoring humans and human-related items: "{prompt_human}". Put that list in the `descriptors` item. In the `ignored` item, put a list of the items from the `descriptors` list that have any relation to humans, human activity or human properties. In the `approved` item, put a list of the items from the `descriptors` list which are not in the `ignore` list, but also include items from the `descriptors` list that relate to style or time. Output only the JSON dictionary, no commentary or explanations."""
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
        return ", ".join(prompt_fallback) + ", no humans"
    except json.decoder.JSONDecodeError:
        logging.warning(f"Invalid non-human prompt: {result}")
        return ""

