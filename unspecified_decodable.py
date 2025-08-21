import os
import re
import math
import openpyxl
import base64
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

OUTPUT_DIR = "generated_book"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

def extract_word_lists(filepath):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active

    mastered_words = []
    target_words = []

    for row in ws.iter_rows(min_row=2):
        for idx in [1, 2, 4]:
            if row[idx].value:
                mastered_words.append(str(row[idx].value).strip())
        for idx in [3, 5]:
            if row[idx].value:
                target_words.append(str(row[idx].value).strip())

    return mastered_words, target_words

def generate_decodable_text(mastered_words, target_words, num_pages=5, extra_instruction=""):
    prompt = f"""
    Write a short children's decodable book.
    Use ONLY these mastered words: {mastered_words}.
    Include and repeat these target learning words: {target_words}.
    Make sure at least 60% of the words in the learning words list are used.
    Make sure at least 80% of the words are mastered words.
    Sentences should be short, simple, and repetitive.
    The book should have {num_pages} pages, each separated by a line containing only '---'.
    {extra_instruction}
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return resp.choices[0].message.content

def analyze_story_words(story_text, mastered_words, target_words):
    words = re.findall(r"\b\w+\b", story_text.lower())
    mastered_set = set(w.lower() for w in mastered_words)
    target_set = set(w.lower() for w in target_words)

    used_mastered = sorted(set(w for w in words if w in mastered_set))
    used_target = sorted(set(w for w in words if w in target_set))

    ratio_mastered = len(used_mastered) / len(mastered_set) if mastered_set else 0
    ratio_target = len(used_target) / len(target_set) if target_set else 0

    return used_mastered, used_target, ratio_mastered, ratio_target

def extract_character_description(story_text):
    """Ask GPT to summarize the main character for consistent illustration."""
    prompt = f"""
    Read the following children's story and describe the MAIN character
    in one concise sentence for use in illustrations.
    Include species/type (e.g. clam, cat, child), colors, clothes, and
    any distinctive features if present.

    Story:
    {story_text}
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    description = resp.choices[0].message.content.strip()
    print(f"Character description extracted: {description}")
    return description

def generate_images_for_story(story_text, client, output_dir, character_description=""):
    pages = [p.strip() for p in story_text.split("---") if p.strip()]
    os.makedirs(output_dir, exist_ok=True)

    for i, page in enumerate(pages, start=1):
        prompt = f"""
        Children's book page. Show the main character {character_description}.
        Create a full illustration in a hand-drawn, cartoonish, bright, child-friendly style.
        At the bottom of the page, include the following text inside a neat white text box 
        with black lettering, sized to fit within the page without cutting off: '{page}'.
        The text should be fully visible, readable, and contained within the image.
        It's necessary that the text does NOT go off the page. 
        """
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )
        img_b64 = response.data[0].b64_json
        image_path = os.path.join(output_dir, f"page_{i}.png")
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(img_b64))
        print(f"Saved image: {image_path}")

def main():
    excel_path = "Updated Child Data Aug12th2015 (1).xlsx"
    mastered_words, target_words = extract_word_lists(excel_path)

    num_pages = 5 
    story_text = generate_decodable_text(mastered_words, target_words, num_pages=num_pages)

    used_mastered, used_target, ratio_mastered, ratio_target = analyze_story_words(
        story_text, mastered_words, target_words
    )

    if ratio_target < 0.6:
        scale_factor = math.ceil(1 / ratio_target)
        num_pages = min(num_pages * scale_factor, 30)  
        print(f"Target ratio too low ({ratio_target:.2f}), regenerating with {num_pages} pages...")

        story_text = generate_decodable_text(
            mastered_words,
            target_words,
            num_pages=num_pages,
            extra_instruction="Please repeat the target words more often and ensure each page includes them."
        )

        used_mastered, used_target, ratio_mastered, ratio_target = analyze_story_words(
            story_text, mastered_words, target_words
        )

    # Extract the main character description for consistent illustrations
    character_description = extract_character_description(story_text)

    output_file = os.path.join(OUTPUT_DIR, "story.txt")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(story_text + "\n\n")
        f.write("Mastered words used:\n")
        f.write(", ".join(used_mastered) + "\n")
        f.write(f"Ratio used / total mastered: {ratio_mastered:.2f}\n\n")
        f.write("Target words used:\n")
        f.write(", ".join(used_target) + "\n")
        f.write(f"Ratio used / total target: {ratio_target:.2f}\n")
        f.write("\nCharacter description for illustrations:\n")
        f.write(character_description + "\n")

    print(f"Story saved to: {output_file}")
    print(f"Used {len(used_mastered)}/{len(mastered_words)} mastered words ({ratio_mastered:.2f})")
    print(f"Used {len(used_target)}/{len(target_words)} target words ({ratio_target:.2f})")

    generate_images_for_story(story_text, client, IMAGES_DIR, character_description)

if __name__ == "__main__":
    main()
