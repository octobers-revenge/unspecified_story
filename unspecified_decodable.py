import os
import openpyxl
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

OUTPUT_DIR = "generated_decodable_stories"
os.makedirs(OUTPUT_DIR, exist_ok=True)

LESSON_FRY_LIMITS = {
    35: 40,    # K mid: First 100 lists 1–4
    48: 60,    # K end: + Second 100 lists 1–2
    57: 80,    # Grade 1 beginning
    80: 120,   # Grade 1 end
    95: 240,   # Grade 2 beginning
    108: 240   # Grade 2 end
}

LESSON_GRADE = {
    35: "K",
    48 : "K",
    60: "1",
    80: "1",
    91: "2",
    120: "2"
}

LESSON_PHASE = {
    # Kindergarten
    35: ("K", "mid"),
    36: ("K", "mid"),
    37: ("K", "mid"),
    39: ("K", "mid"),
    40: ("K", "mid"),
    42: ("K", "end"),
    43: ("K", "end"),
    44: ("K", "end"),
    45: ("K", "end"),
    46: ("K", "end"),
    47: ("K", "end"),
    48: ("K", "end"),

    # Grade 1
    54: ("1", "beginning"),
    55: ("1", "beginning"),
    56: ("1", "beginning"),
    57: ("1", "beginning"),
    58: ("1", "beginning"),

    66: ("1", "mid"),
    67: ("1", "mid"),
    68: ("1", "mid"),
    69: ("1", "mid"),
    70: ("1", "mid"),

    77: ("1", "end"),
    78: ("1", "end"),
    80: ("1", "end"),
    81: ("1", "end"),
    84: ("1", "end"),
    85: ("1", "end"),

    # Grade 2
    91: ("2", "beginning"),
    93: ("2", "beginning"),
    94: ("2", "beginning"),
    95: ("2", "beginning"),
    96: ("2", "beginning"),

    98: ("2", "mid"),
    99: ("2", "mid"),
    100: ("2", "mid"),
    101: ("2", "mid"),
    102: ("2", "mid"),
    103: ("2", "mid"),
    104: ("2", "mid"),

    108: ("2", "end"),
    109: ("2", "end"),
    110: ("2", "end"),
    111: ("2", "end"),
    112: ("2", "end"),
    113: ("2", "end"),
    114: ("2", "end"),
    115: ("2", "end"),
    116: ("2", "end"),
    117: ("2", "end"),
    118: ("2", "end"),
    119: ("2", "end"),
    120: ("2", "end"),
    121: ("2", "end"),
    122: ("2", "end"),
    123: ("2", "end"),
    124: ("2", "end"),
    125: ("2", "end"),
    126: ("2", "end"),
    127: ("2", "end"),
}

STORY_EXPECTATIONS = {
    ("K", "mid"): {
        "sentences": "8–10",
        "target_repeats": "about 5"
    },
    ("K", "end"): {
        "sentences": "12–15",
        "target_repeats": "about 5"
    },
    ("1", "beginning"): {
        "sentences": "15–18",
        "target_repeats": "about 8"
    },
    ("1", "mid"): {
        "sentences": "18–22",
        "target_repeats": "about 8"
    },
    ("1", "end"): {
        "sentences": "22–25",
        "target_repeats": "about 8"
    },
    ("2", "beginning"): {
        "sentences": "25–28",
        "target_repeats": "about 10"
    },
    ("2", "mid"): {
        "sentences": "28–32",
        "target_repeats": "about 10"
    },
    ("2", "end"): {
        "sentences": "32–35",
        "target_repeats": "about 10"
    }
}


def load_fry_words(filepath="Word Lists/1000words.txt", limit=100):
    with open(filepath, "r", encoding="utf-8") as f:
        words = [line.strip().lower() for line in f if line.strip()]
    return words[:limit]


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


def generate_decodable_text(
    fry_words,
    review_words,
    target_words,
    phonics_class,
    grade,
    phase,
    sentence_range,
    target_repeat_guidance
):
    prompt = f"""
Write a short decodable narrative story aligned to UFLI phonics lesson {phonics_class}.

Grade level: Grade {grade}, {phase} of the school year.

Story requirements:
- Use ONLY words from these two sources:
  • Fry sight words (grade-appropriate): {fry_words}
  • Words from previous phonics lessons: {review_words}
- The target words {target_words} must appear naturally several times.
- You may add other simple decodable words ONLY if they follow the current
  phonics pattern for this lesson (e.g., VC, CVC, CVCC, etc.).
- Avoid any long, abstract, or multi-syllable words.
- Names need to use the phonics patterns of this lesson.

Story length:
- Write {sentence_range} total sentences.

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

  Page structure expectations:
- Kindergarten: about 1 sentence per page
- Grade 1: about 2–3 sentences per page
- Grade 2: about 4–5 sentences per page
(Do not label pages.)

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

def revise_story_to_meet_rubric(story_text):
    rubric_prompt = f"""
You are evaluating a narrative story for children using the rubric below.

Meaning Analysis for Narrative Text

Criterion: Word Meaning Complexity
- Ideal: 1–2 words for which children likely do not know meanings (these are supported by context)
- Moderate: 3–4 words for which children likely do not know meanings (these are supported by context)
- Poor: 5+ words for which children likely do not know meanings (these are supported by context)

Criterion: Narrative Elements
- Ideal: The story has all of the following — clear characters, setting, problem, events, and solution.
- Moderate: The story has all but one of the following — clear characters, setting, problem, events, and solution.
- Poor: The story is missing two or more of the following — clear characters, setting, problem, events, and solution.

Criterion: Event Sequence
- Ideal: Includes a meaningfully interconnected sequence of events with no disconnected events.
- Moderate: Includes meaningfully connected and appropriately sequenced events but may include 1–2 disconnected events.
- Poor: Includes two or more disconnected events that are not meaningfully sequenced.

Criterion: Oral Language Register
- Ideal: The text sounds like how people talk.
- Moderate: The text sounds mostly like how people talk, with a few odd phrases or sentences.
- Poor: The text does NOT sound like how people talk, or more than three phrases or sentences sound odd.

Task:
1. Evaluate the story and determine whether each criterion is Ideal, Moderate, or Poor.
2. If ALL criteria are Ideal, return the story unchanged.
3. If ANY criterion is Moderate or Poor, revise the story so that ALL criteria meet the Ideal level.

Revision rules:
- Do NOT add advanced or abstract vocabulary.
- Do NOT increase word meaning complexity.
- Keep the story decodable.
- Keep phonics patterns intact.
- Keep sentences short and natural.
- Remove or rewrite disconnected events.
- Clarify missing narrative elements if needed.

Output ONLY the final revised story.

Story:
{story_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": rubric_prompt}],
    )

    return response.choices[0].message.content.strip()



def main():
    lessons = [35, 48, 60, 80, 91, 120]  

    for lesson_num in lessons:
        print(f"Generating story for UFLI lesson {lesson_num}...")

        fry_limit = LESSON_FRY_LIMITS.get(lesson_num, 40)  # default to 40 if missing
        fry_words = load_fry_words(limit=fry_limit)


        review_words = load_previous_phonics_words(
            "phonics_lessons.xlsx",
            lesson_num=lesson_num
        )

        # Load lesson rule and target words
        rule, target_words = load_phonics_lesson(
            "phonics_lessons.xlsx",
            lesson_num=lesson_num
        )

        # Get grade and phase
        if lesson_num in LESSON_PHASE:
            grade, phase = LESSON_PHASE[lesson_num]
        else:
            grade, phase = LESSON_GRADE.get(lesson_num, "K"), "mid"

        # Get story expectations (sentence count & target repeats)
        sentence_range = STORY_EXPECTATIONS[(grade, phase)]["sentences"]
        target_repeat_guidance = STORY_EXPECTATIONS[(grade, phase)]["target_repeats"]

        #story generation call
        story_text = generate_decodable_text(
            fry_words=fry_words,
            review_words=review_words,
            target_words=target_words,
            phonics_class=lesson_num,
            grade=grade,
            phase=phase,
            sentence_range=sentence_range,
            target_repeat_guidance=target_repeat_guidance
        )

        # Revise story to meet rubric
        # story_text = revise_story_to_meet_rubric(story_text)

        # Save story
        story_dir = os.path.join(OUTPUT_DIR, f"Lesson_{lesson_num}")
        os.makedirs(story_dir, exist_ok=True)

        with open(os.path.join(story_dir, "story.txt"), "w", encoding="utf-8") as f:
            f.write(f"UFLI Lesson {lesson_num}: {rule}\n\n")
            f.write(story_text)

        print(f"Saved story for lesson {lesson_num}\n")

if __name__ == "__main__":
    main()





