import os
import json
import base64
from dotenv import load_dotenv
from openai import OpenAI
from rubrics2 import text_rubric, image_rubric

# Where evaluation results will be stored
EVAL_PATH = "evaluations"
os.makedirs(EVAL_PATH, exist_ok=True)

VERBOSE = True

BASE_PROMPTS = {
    "text_eval": """
You are an expert children's story editor. According to the given rubric, you must assess the
quality of the given story text. For each rubric area:
- The first item is worth 3 points, the second 2, the third 1 (higher is better).
- Be very strict: Only give a score of 3 if the story perfectly and fully meets the highest standard for that category. Any minor lapse should earn a 2, and any greater issue should earn a 1.
- Be especially critical and detailed in the areas of word usage, complexity, and sentence/page length. Point out any weaknesses or inconsistencies, even minor ones.
- Reference the rubric in your justification.
- Use specific examples from the story to support your score.
- Low scores are not bad; they help identify areas for improvement.

Return the response in this exact JSON format:
[
    {
        "category": "Language Simplicity",
        "score": "2",
        "justification": "explanation"
    },
    ...
    {
        "category": "Total Score",
        "score": "25",
        "justification": "Overall evaluation of the story"
    },
]
""",
    "image_eval": """
You are an expert children's story editor. According to the given story text and rubric, you must assess the quality of
the given story images. For each rubric area:
- The first item is worth 3 points, the second 2, the third 1 (higher is better).
- Be very strict: Only give a score of 3 if the image perfectly and fully meets the highest standard for that category. Any minor lapse should earn a 2, and any greater issue should earn a 1.
- Be especially critical and detailed in the areas of character consistency and narrative relevance. Point out any weaknesses or inconsistencies, even minor ones.
- Reference the rubric and the story text in your justification.
- Use specific examples from the images and story to support your score.
- Low scores are not bad; they help identify areas for improvement.

Return the response in this exact JSON format:
[
    {
        "category": "Character Consistency",
        "score": "2",
        "justification": "explanation"
    },
    ...
    {
        "category": "Total Score",
        "score": "25",
        "justification": "Overall evaluation of the story images"
    },
]
""",
}

def read_story_from_file(story_path: str) -> str:
    """Read raw story text from file (your generated story.txt)."""
    with open(story_path, "r", encoding="utf-8") as f:
        return f.read()

def read_story_images(image_dir: str) -> dict[str, str]:
    """Read all images in a directory as base64 strings."""
    if not os.path.isdir(image_dir):
        raise ValueError(f"{image_dir} is not a valid directory.")

    images = {}
    for filename in sorted(os.listdir(image_dir)):
        full_path = os.path.join(image_dir, filename)
        if os.path.isfile(full_path) and filename.lower().endswith((".png", ".jpg", ".jpeg")):
            with open(full_path, "rb") as f:
                images[filename] = base64.b64encode(f.read()).decode("utf-8")

    return images

def eval_text(client: OpenAI, story_path: str):
    if VERBOSE:
        print("- " * 80)
        print(f"Evaluating Text for {story_path}\n")

    story_text = read_story_from_file(story_path)

    prompt = (
        f"This is your rubric:\n"
        f"{text_rubric}\n"
        f"This is the story you must evaluate:\n"
        f"{story_text}"
    )

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": BASE_PROMPTS["text_eval"]},
            {"role": "user", "content": prompt},
        ],
    )

    eval_path = os.path.join(EVAL_PATH, os.path.basename(story_path).replace(".txt", "__text_eval.json"))
    with open(eval_path, "w", encoding="utf-8") as f:
        f.write(response.output_text)

    if VERBOSE:
        print(f"Saved text evaluation to {eval_path}")

def eval_images(client: OpenAI, story_path: str, image_dir: str):
    if VERBOSE:
        print("- " * 80)
        print(f"Evaluating Images for {image_dir}\n")

    story_text = read_story_from_file(story_path)

    prompt = (
        f"This is your rubric:\n"
        f"{image_rubric}\n"
        f"This is the story:\n"
        f"{story_text}\n"
    )

    story_images = read_story_images(image_dir)
    images_content = [
        {"type": "input_image", "image_url": f"data:image/png;base64,{image}"}
        for image in story_images.values()
    ]

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": BASE_PROMPTS["image_eval"]},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    *images_content,
                ],
            },
        ],
    )

    eval_path = os.path.join(EVAL_PATH, os.path.basename(story_path).replace(".txt", "__image_eval.json"))
    with open(eval_path, "w", encoding="utf-8") as f:
        f.write(response.output_text)

    if VERBOSE:
        print(f"Saved image evaluation to {eval_path}")

def main():
    load_dotenv()
    client = OpenAI()

    story_path = r"C:\Users\atn12\Downloads\new_story\story.txt"
    image_dir = r"C:\Users\atn12\Downloads\new_story"

    eval_text(client, story_path)
    eval_images(client, story_path, image_dir)

if __name__ == "__main__":
    main()