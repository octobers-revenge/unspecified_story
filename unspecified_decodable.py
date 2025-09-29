import os
import re
import openpyxl
import base64
from io import BytesIO
from dotenv import load_dotenv
from openai import OpenAI
import random

load_dotenv()
client = OpenAI()

OUTPUT_DIR = "generated_book_texts"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_fry_words(filepath="Word Lists/1000words.txt", grade="K"):
    fry_counts = {"K": 150, "1": 300, "2": 450}
    n = fry_counts.get(grade, 150)
    with open(filepath, "r", encoding="utf-8") as f:
        all_fry = [line.strip().lower() for line in f if line.strip()]
    return all_fry[:n]


def load_combined_base_words(folder="Word Lists", grade="K"):
    grade_files = {
        "K": ("kindergartenAOA.txt", "KindergartenWordList.txt"),
        "1": ("grade1AOA.txt", "FirstGradeWordList.txt"),
        "2": ("grade2AOA.txt", "SecondGradeWordList.txt"),
    }

    aoa_file, dolch_file = grade_files.get(grade, ("kindergartenAOA.txt", "KindergartenWordList.txt"))
    combined = set()
    for fname in [aoa_file, dolch_file]:
        path = os.path.join(folder, fname)
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    combined.add(word)

    fry_words = load_fry_words("Word Lists/1000words.txt", grade)
    combined.update(fry_words)
    return list(combined)


def load_phonics_lesson(filepath="phonics_lessons.xlsx", lesson_num=1):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[1]
    row = ws[lesson_num + 1]
    rule = row[0].value
    words_raw = row[1].value
    target_words = [w.strip() for w in words_raw.split(",") if w.strip()]
    return rule, target_words


def load_cumulative_mastered_words(filepath="phonics_lessons.xlsx", lesson_num=1, grade="K"):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[1]
    mastered = set(load_combined_base_words(grade=grade))
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
        temperature=0.7,
    )
    return resp.choices[0].message.content


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
        temperature=0.3,
    )
    description = resp.choices[0].message.content.strip()
    print(f"Character description extracted: {description}")
    return description


def generate_main_character_image(client, character_description, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    prompt = f"""
Create a full-body illustration of the main character for a children's book.
Character description: {character_description}.
Style: hand-drawn, cartoonish, bright, child-friendly.
No text in the image.
"""
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
    )
    img_b64 = response.data[0].b64_json
    character_path = os.path.join(output_dir, "main_character.png")
    with open(character_path, "wb") as f:
        f.write(base64.b64decode(img_b64))
    print(f"Saved main character reference image: {character_path}")
    return character_path


def generate_images_for_story(story_text, client, output_dir, character_description, character_ref_path):
    pages = [p.strip() for p in story_text.split("---") if p.strip()]
    os.makedirs(output_dir, exist_ok=True)

    with open(character_ref_path, "rb") as f:
        character_image_bytes = f.read()
    character_image_io = BytesIO(character_image_bytes)
    character_image_io.name = "main_character.png"

    for i, page in enumerate(pages, start=1):
        prompt = f"""
Illustrate this children's book page:
Page text: {page}
Always show the main character (consistent with the reference image).
Style: hand-drawn, cartoonish, bright, child-friendly.
No text in the illustration.
"""
        response = client.images.edit(
            model="gpt-image-1",
            prompt=prompt,
            image=[character_image_io],
            size="1536x1024",
            quality="medium",
        )

        img_b64 = response.data[0].b64_json
        image_path = os.path.join(output_dir, f"page_{i}.png")
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(img_b64))
        print(f"Saved image: {image_path}")


def main():
    grades = ["K", "1", "2"]
    stories_per_grade = 5
    num_pages = 5
    lesson_min, lesson_max = 1, 34  # Random lesson range

    for grade in grades:
        for i in range(1, stories_per_grade + 1):
            lesson_num = random.randint(lesson_min, lesson_max)
            print(f"Generating story {i} for Grade {grade}, Lesson {lesson_num}...")

            # Load words
            base_words = load_combined_base_words("Word Lists", grade=grade)
            mastered_words = load_cumulative_mastered_words("phonics_lessons.xlsx", lesson_num=lesson_num, grade=grade)
            review_words = load_previous_phonics_words("phonics_lessons.xlsx", lesson_num=lesson_num)
            rule, target_words = load_phonics_lesson("phonics_lessons.xlsx", lesson_num=lesson_num)

            # Generate story text
            story_text = generate_decodable_text(
                mastered_words, review_words, target_words,
                phonics_class=lesson_num, num_pages=num_pages
            )

            # Extract character description
            character_description = extract_character_description(story_text)

            # Prepare story folder
            story_dir = os.path.join(OUTPUT_DIR, f"Grade_{grade}", f"Story_{i}")
            os.makedirs(story_dir, exist_ok=True)

            # Save story text
            story_file = os.path.join(story_dir, "story.txt")
            with open(story_file, "w", encoding="utf-8") as f:
                f.write(f"Phonics Lesson {lesson_num}: {rule}\n\n")
                f.write(story_text + "\n\n")
                f.write("Character description:\n")
                f.write(character_description + "\n")

            images_dir = os.path.join(story_dir, "images")
            os.makedirs(images_dir, exist_ok=True)

            character_ref_path = generate_main_character_image(client, character_description, images_dir)

            generate_images_for_story(story_text, client, images_dir, character_description, character_ref_path)

            print(f"Finished story {i} for Grade {grade}, Lesson {lesson_num}.\n")


if __name__ == "__main__":
    main()



