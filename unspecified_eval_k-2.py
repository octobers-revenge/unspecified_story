import os
import json
import base64
from dotenv import load_dotenv
from openai import OpenAI


# Where evaluation results will be stored
EVAL_PATH = "evaluations"
os.makedirs(EVAL_PATH, exist_ok=True)


VERBOSE = True


# Expanded rubrics (embedded directly into code)
TEXT_RUBRIC = """
### Text Rubric for K–2 Phonics Story Evaluation
- **Phonics Integration**: Must use 3–5 words from the target phonics pattern naturally.
- **Readability**: Mostly Fry top 100 words; short sentences (5–10 words max); total length ~100–200 words.
- **Simplicity & Structure**: One clear setting, 1–2 characters; beginning–middle–end progression; repetition for reinforcement.
- **Engagement**: Fun, silly, relatable events (animals, school, friends, food); ends with a resolution or happy note.
- **Tone**: Friendly, playful, encouraging; avoid sarcasm or abstract themes.


Scoring (strict):
- 3 = Perfectly fulfills the criterion
- 2 = Minor issues
- 1 = Major issues
"""


IMAGE_RUBRIC = """
### Image Rubric for K–2 Phonics Story Evaluation
- **Alignment with Text**: Must show at least one target word concept; matches story events.
- **Clarity**: Bold, simple shapes; clear outlines; minimal clutter.
- **Consistency**: Same characters retain identity; style stays cartoonish, bright, friendly.
- **Engagement**: Playful details (cat peeking, balloon, funny face); show action or emotion.
- **Accessibility**: Scene is understandable without text; high contrast, easy to parse.


Scoring (strict):
- 3 = Perfectly fulfills the criterion
- 2 = Minor issues
- 1 = Major issues
"""


BASE_PROMPTS = {
"text_eval": f"""
You are an expert children's story editor. According to the rubric below, assess the quality of the given story text.
Rubric:
{TEXT_RUBRIC}


Return the response in this exact JSON format:
[
{{"category": "Phonics Integration", "score": "2", "justification": "..."}},
...
{{"category": "Total Score", "score": "12", "justification": "Overall evaluation"}}
]
Be strict. Use examples from the story to justify.
""",


"image_eval": f"""
You are an expert children's story editor. According to the rubric below, assess the quality of the story illustrations.
Rubric:
{IMAGE_RUBRIC}


Return the response in this exact JSON format:
[
{{"category": "Alignment with Text", "score": "2", "justification": "..."}},
...
{{"category": "Total Score", "score": "12", "justification": "Overall evaluation of images"}}
]
Be strict. Use specific references to both text and images.
""",
}


def read_story_from_file(story_path: str) -> str:

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
    story_text = read_story_from_file(story_path)

    prompt = (
        f"This is your rubric:\n{TEXT_RUBRIC}\n"
        f"This is the story you must evaluate:\n{story_text}"
    )

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": BASE_PROMPTS["text_eval"]},
            {"role": "user", "content": prompt},
        ],
    )

    eval_path = os.path.join(
        EVAL_PATH, os.path.basename(story_path).replace(".txt", "__text_eval.json")
    )
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
        f"This is your rubric:\n{IMAGE_RUBRIC}\n"
        f"This is the story:\n{story_text}\n"
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

    eval_path = os.path.join(
        EVAL_PATH, os.path.basename(story_path).replace(".txt", "__image_eval.json")
    )
    with open(eval_path, "w", encoding="utf-8") as f:
        f.write(response.output_text)

    if VERBOSE:
        print(f"Saved image evaluation to {eval_path}")


def main():
    load_dotenv()
    client = OpenAI()

    # Update with your story + image paths
    story_path = r"C:\Users\atn12\Downloads\unspecified_story\generated_book\story.txt"
    image_dir = r"C:\Users\atn12\Downloads\unspecified_story\generated_book\images"

    eval_text(client, story_path)
    eval_images(client, story_path, image_dir)


if __name__ == "__main__":
    main()
