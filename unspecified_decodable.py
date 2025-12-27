import os
import openpyxl
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

OUTPUT_DIR = "generated_decodable_stories"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# Fry word limits by UFLI lesson (from spreadsheet)
# --------------------------------------------------
LESSON_FRY_LIMITS = {
    37: 40,    # K mid: First 100 lists 1–4
    48: 60,    # K end: + Second 100 lists 1–2
    57: 80,    # Grade 1 beginning
    80: 120,   # Grade 1 end
    95: 240,   # Grade 2 beginning
    108: 240   # Grade 2 end
}

LESSON_GRADE = {
    37: "K",
    48: "K",
    57: "1",
    80: "1",
    95: "2",
    108: "2"
}

# --------------------------------------------------
# Load Fry words (explicit limit)
# --------------------------------------------------
def load_fry_words(filepath="Word Lists/1000words.txt", limit=100):
    with open(filepath, "r", encoding="utf-8") as f:
        words = [line.strip().lower() for line in f if line.strip()]
    return words[:limit]

# --------------------------------------------------
# Load phonics lessons
# --------------------------------------------------
def load_phonics_lesson(filepath="phonics_lessons.xlsx", lesson_num=35):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[1]
    row = ws[lesson_num + 1]
    rule = row[0].value
    words_raw = row[1].value
    target_words = [w.strip().lower() for w in words_raw.split(",") if w.strip()]
    return rule, target_words

def load_previous_phonics_words(filepath="phonics_lessons.xlsx", lesson_num=35):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[1]
    review_words = set()
    for ln in range(1, lesson_num):
        row = ws[ln + 1]
        words_raw = row[1].value
        if words_raw:
            review_words.update(
                w.strip().lower() for w in words_raw.split(",") if w.strip()
            )
    return list(review_words)

# --------------------------------------------------
# Text generation
# --------------------------------------------------
def generate_decodable_text(fry_words, review_words, target_words, phonics_class):
    prompt = f"""
Write a short decodable narrative story aligned to UFLI phonics lesson {phonics_class}.

Story requirements:
- Use ONLY words from these two sources:
  • Fry sight words (grade-appropriate): {fry_words}
  • Words from previous phonics lessons: {review_words}
- The target words {target_words} must appear naturally several times.
- You may add other simple decodable words ONLY if they follow the current
  phonics pattern for this lesson (e.g., VC, CVC, CVCC, etc.).
- Avoid any long, abstract, or multi-syllable words.
- Names need to use the phonics patterns of this lesson.
- Around 15 sentences per story.

Structure and storytelling requirements:
- Write a complete short story.
- The story must have:
  • a clear beginning (introduce characters and setting),
  • a middle (a simple problem, goal, or event),
  • an end (the problem is solved or the goal is met).
- Keep ONE clear main idea or event throughout the story.
- Each sentence must connect logically to the sentence before it.
- Characters should act in consistent, realistic ways.
- Introduce new characters, objects, or settings only when needed
  and explain them through simple actions.

Language and tone:
- Sentences should sound natural when read aloud by a young reader.
- Use clear, concrete actions (run, sit, get, look, help, find).
- Use simple words or phrases that suggest feelings or actions
  (e.g., sad, glad, mad), when decodable.
- Do NOT use figurative language, advanced vocabulary, or abstract ideas.

Model your writing on the tone, simplicity, and structure of the examples below,
but do NOT copy their wording or events.

Example:
Min has a kit.
Kim has a lid.
They dig in the big pit.
“Dig, Min! Dig, Kim!”
A bug is in the pit.
The bug is big and red.
Min can lift the lid.
Kim can pin the bug in the kit.
The bug will not slip.
“Look, Kim! We did it!” said Min.
Kim had a big grin.
They put the bug in the kit.
Min, Kim, and the bug sit in the sun.
They had fun and did a big job.

Example 2:
Jan had a cat.
The cat was Sam.
Sam sat on Jan’s lap.

Jan had a map.
“It is a map of the park,” said Jan.
“I can run and hop at the park!”

Sam ran to the map.
Sam sat on it.
“Oh, Sam!” said Jan. “That is my map!”

Jan got the map.
Sam ran to the mat.
Jan ran to Sam.

“Let’s go, Sam!” said Jan.
Jan and Sam ran and ran.
They ran up a path.
They ran past a big rock.

At last, they sat and had a nap.
Jan had fun.
Sam had fun.

Output the story as plain text, with one sentence per line.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


# --------------------------------------------------
# Main: generate 6 stories
# --------------------------------------------------
def main():
    lessons = [37, 48, 57, 80, 95, 108]

    for lesson_num in lessons:
        print(f"Generating story for UFLI lesson {lesson_num}...")

        fry_limit = LESSON_FRY_LIMITS[lesson_num]
        fry_words = load_fry_words(limit=fry_limit)

        review_words = load_previous_phonics_words(
            "phonics_lessons.xlsx",
            lesson_num=lesson_num
        )

        rule, target_words = load_phonics_lesson(
            "phonics_lessons.xlsx",
            lesson_num=lesson_num
        )

        story_text = generate_decodable_text(
        fry_words=fry_words,              # FIX: explicit Fry list
        review_words=review_words,         # phonics words
        target_words=target_words,
        phonics_class=lesson_num
)

        story_dir = os.path.join(OUTPUT_DIR, f"Lesson_{lesson_num}")
        os.makedirs(story_dir, exist_ok=True)

        with open(os.path.join(story_dir, "story.txt"), "w", encoding="utf-8") as f:
            f.write(f"UFLI Lesson {lesson_num}: {rule}\n\n")
            f.write(story_text)

        print(f"Saved story for lesson {lesson_num}\n")

if __name__ == "__main__":
    main()





