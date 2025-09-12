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

def load_base_words(filepath="mixedwords.txt"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        words = [w.strip().lower() for w in content.split(",") if w.strip()]
    return words

def load_phonics_lesson(filepath="phonics_lessons.xlsx", lesson_num=1):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[1]
    row = ws[lesson_num + 1]
    rule = row[0].value
    words_raw = row[1].value
    target_words = [w.strip() for w in words_raw.split(",") if w.strip()]
    return rule, target_words

def load_cumulative_mastered_words(filepath="phonics_lessons.xlsx", lesson_num=1):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[1]
    mastered = set(load_base_words())
    for ln in range(1, lesson_num):
        row = ws[ln + 1]
        words_raw = row[1].value
        if words_raw:
            words = [w.strip().lower() for w in words_raw.split(",") if w.strip()]
            mastered.update(words)
    return list(mastered)

def load_previous_phonics_words(filepath="phonics_lessons.xlsx", lesson_num=1):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[1]
    review_words = set()
    for ln in range(1, lesson_num):
        row = ws[ln + 1]
        words_raw = row[1].value
        if words_raw:
            words = [w.strip().lower() for w in words_raw.split(",") if w.strip()]
            review_words.update(words)
    return list(review_words)

def generate_decodable_text(mastered_words, review_words, target_words, phonics_class, num_pages=5):
    prompt = f"""
    Write a short children's decodable book for UFLI phonics class {phonics_class}.
    Use only words from the mastered/base word list: {mastered_words}, 
    or the review words from past phonics lessons: {review_words}, 
    except for the target words for this lesson: {target_words}, which must appear.
    Include a few review words naturally, but do not introduce any extra words outside of these lists.
    Sentences should be simple and repetitive, suitable for K–2 readers.
    The book should have a main character performing actions.
    The book should have {num_pages} pages, each separated by '---'.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return resp.choices[0].message.content

def analyze_story_words(story_text, base_words, review_words, target_words):
    words = re.findall(r"\b\w+\b", story_text.lower())
    base_set = set(w.lower() for w in base_words)
    review_set = set(w.lower() for w in review_words)
    target_set = set(w.lower() for w in target_words)

    used_base = sorted(set(w for w in words if w in base_set))
    used_review = sorted(set(w for w in words if w in review_set))
    used_target = sorted(set(w for w in words if w in target_set))

    ratio_base = len(used_base) / len(base_set) if base_set else 0
    ratio_review = len(used_review) / len(review_set) if review_set else 0
    ratio_target = len(used_target) / len(target_set) if target_set else 0

    overall_freq = (len(used_base) + len(used_review) + len(used_target)) / max(1, len(words))
    return used_base, used_review, used_target, ratio_base, ratio_review, ratio_target, overall_freq

def extract_character_description(story_text):
    prompt = f"""
    Read the following children's story and describe the MAIN character in one concise sentence for illustrations.
    Include species/type, colors, clothes, and distinctive features if present.
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
        Illustrate this children's book page:

        Page text: {page}

        Show the main character: {character_description}.
        Include all actions and interactions described on this page.
        Style: hand-drawn, cartoonish, bright, child-friendly.
        No text should appear in the illustration.
        """
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1536x1024"
        )
        img_b64 = response.data[0].b64_json
        image_path = os.path.join(output_dir, f"page_{i}.png")
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(img_b64))
        print(f"Saved image: {image_path}")

def main():
    lesson_num = 9
    base_words = load_base_words("mixedwords.txt")
    mastered_words = load_cumulative_mastered_words("phonics_lessons.xlsx", lesson_num)
    review_words = load_previous_phonics_words("phonics_lessons.xlsx", lesson_num)
    rule, target_words = load_phonics_lesson("phonics_lessons.xlsx", lesson_num)

    num_pages = 5
    story_text = generate_decodable_text(
        mastered_words, review_words, target_words,
        phonics_class=lesson_num, num_pages=num_pages
    )

    used_base, used_review, used_target, ratio_base, ratio_review, ratio_target, freq_score = analyze_story_words(
        story_text, base_words, review_words, target_words
    )

    character_description = extract_character_description(story_text)

    output_file = os.path.join(OUTPUT_DIR, "story.txt")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Phonics Lesson {lesson_num}: {rule}\n\n")
        f.write(story_text + "\n\n")
        f.write("Base/mastered words used:\n")
        f.write(", ".join(used_base) + "\n")
        f.write(f"Ratio used / total base words: {ratio_base:.2f}\n\n")
        f.write("Review words from old phonics patterns used:\n")
        f.write(", ".join(used_review) + "\n")
        f.write(f"Ratio used / total review words: {ratio_review:.2f}\n\n")
        f.write("Target words used:\n")
        f.write(", ".join(used_target) + "\n")
        f.write(f"Ratio used / total target words: {ratio_target:.2f}\n")
        f.write("\nCharacter description for illustrations:\n")
        f.write(character_description + "\n")

    print(f"Story saved to: {output_file}")
    print(f"Used {len(used_base)}/{len(base_words)} base words ({ratio_base:.2f})")
    print(f"Used {len(used_review)}/{len(review_words)} review words ({ratio_review:.2f})")
    print(f"Used {len(used_target)}/{len(target_words)} target words ({ratio_target:.2f})")
    print(f"Overall frequency of mastered/review/target words in story: {freq_score:.2f}")

    generate_images_for_story(story_text, client, IMAGES_DIR, character_description)

if __name__ == "__main__":
    main()
