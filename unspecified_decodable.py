import os
import re
import openpyxl
import random
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

OUTPUT_DIR = "generated_first_grade_texts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Loaders (unchanged except fixed grade to "1") ---
def load_fry_words(filepath="Word Lists/1000words.txt", grade="1"):
    fry_counts = {"K": 150, "1": 300, "2": 450}
    n = fry_counts.get(grade, 300)
    with open(filepath, "r", encoding="utf-8") as f:
        all_fry = [line.strip().lower() for line in f if line.strip()]
    return all_fry[:n]


def load_combined_base_words(folder="Word Lists", grade="1"):
    grade_files = {
        "1": ("grade1AOA.txt", "FirstGradeWordList.txt"),
    }
    aoa_file, dolch_file = grade_files["1"]
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


def load_phonics_lesson(filepath="phonics_lessons.xlsx", lesson_num=35):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[1]
    row = ws[lesson_num + 1]
    rule = row[0].value
    words_raw = row[1].value
    target_words = [w.strip() for w in words_raw.split(",") if w.strip()]
    return rule, target_words


def load_cumulative_mastered_words(filepath="phonics_lessons.xlsx", lesson_num=35, grade="1"):
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


def load_previous_phonics_words(filepath="phonics_lessons.xlsx", lesson_num=35):
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


# --- Text generation only ---
def generate_decodable_text(mastered_words, review_words, target_words, phonics_class):
    prompt = f"""
Write a short decodable story for **first grade** using UFLI phonics lesson {phonics_class}.
This is a short "o" review lesson (VC, CVC, and CVCC patterns like dog, log, mom, fox).

Story requirements:
- Use only words from the mastered list: {mastered_words}, 
  or review words from past lessons: {review_words}.
- The target words {target_words} must appear naturally several times.
- You may add other simple short-o words (VC, CVC, or CVCC) only if needed for clarity.
- Each sentence should be 4–6 words long.
- Write exactly **15 sentences**.
- The story must make sense and flow clearly — with a beginning, middle, and end.
- Keep one main idea or event throughout (for example: a cat gets a snack, or a kid plays in the sand).
- Characters should only be introduced at the beginning of the story.
- New objects and elements should be introduced naturally.
- Sentences should sound natural when read aloud by a first grader.
- Avoid any long, abstract, or multi-syllable words (e.g., "adventure", "family", "happy", "forest").
- Use simple and clear actions. Each sentence should connect to the next.
- All the names of the characters should use the targeted phonics pattern

Output the story as plain text, with one sentence per line.




Output the story as plain text, with one sentence per line.
"""
    resp = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()



# --- Main (fixed to only 1st grade, Lesson 35) ---
def main():
    grade = "1"
    lesson_num = 37
    num_stories = 1

    for i in range(1, num_stories + 1):
        print(f"Generating story {i} for Grade {grade}, Lesson {lesson_num}...")

        mastered_words = load_cumulative_mastered_words("phonics_lessons.xlsx", lesson_num=lesson_num, grade=grade)
        review_words = load_previous_phonics_words("phonics_lessons.xlsx", lesson_num=lesson_num)
        rule, target_words = load_phonics_lesson("phonics_lessons.xlsx", lesson_num=lesson_num)

        story_text = generate_decodable_text(mastered_words, review_words, target_words, phonics_class=lesson_num)

        story_dir = os.path.join(OUTPUT_DIR, f"Story_{i}")
        os.makedirs(story_dir, exist_ok=True)
        story_file = os.path.join(story_dir, "story.txt")

        with open(story_file, "w", encoding="utf-8") as f:
            f.write(f"Phonics Lesson {lesson_num}: {rule}\n\n")
            f.write(story_text + "\n")

        print(f"Saved text-only story {i} in {story_dir}\n")


if __name__ == "__main__":
    main()




