import os
import re
import openpyxl
import base64
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

OUTPUT_DIR = "generated_book"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)



def load_fry_words(filepath="1000words.txt", top_n=100):
    with open(filepath, "r", encoding="utf-8") as f:
        fry_list = [w.strip().lower() for w in f if w.strip()]
    return fry_list[:top_n]

def load_phonics_lesson(filepath="phonics_lessons.xlsx", lesson_num=1):
    """Load target words for a given UFLI lesson (Sheet2)."""
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[1]  # Sheet2 (Python index 1)

    row = ws[lesson_num + 1]  # row 2 = lesson 1, so lesson_num + 1
    rule = row[0].value
    words_raw = row[1].value
    target_words = [w.strip() for w in words_raw.split(",") if w.strip()]

    return rule, target_words


def generate_decodable_text(mastered_words, target_words, phonics_class, num_pages=5):
    prompt = f"""
    Write a short children's decodable book for UFLI phonics class {phonics_class}.
    Known words (previously mastered, high frequency): {mastered_words}.
    Target phonics words (focus for this lesson): {target_words}.
    Sentences should be short, simple, and repetitive.
    The book should have {num_pages} pages, each separated by a line containing only '---'.
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

    return used_mastered, used_target, ratio_mastered, ratio_target, (len(used_mastered) + len(used_target)) / max(1, len(words))

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
    mastered_words = load_fry_words("1000words.txt", top_n=100)

    lesson_num = 7  # Example: lesson 7 = row 8 in Excel
    rule, target_words = load_phonics_lesson("phonics_lessons.xlsx", lesson_num)

    num_pages = 5
    story_text = generate_decodable_text(mastered_words, target_words, phonics_class=lesson_num, num_pages=num_pages)

    used_mastered, used_target, ratio_mastered, ratio_target, freq_score = analyze_story_words(
        story_text, mastered_words, target_words
    )

    character_description = extract_character_description(story_text)


    output_file = os.path.join(OUTPUT_DIR, "story.txt")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Phonics Lesson {lesson_num}: {rule}\n\n")
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
    print(f"Overall frequency of mastered/target words in story: {freq_score:.2f}")

    generate_images_for_story(story_text, client, IMAGES_DIR, character_description)

if __name__ == "__main__":
    main()
