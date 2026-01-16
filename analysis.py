import openpyxl
import pronouncing
import string

# --------------------------------------------------
# Fry word limits by UFLI lesson
# --------------------------------------------------
LESSON_FRY_LIMITS = {
    35: 40,
    48: 60,
    57: 80,
    80: 120,
    95: 240,
    108: 240
}

# --------------------------------------------------
# UFLI lesson → target phoneme mapping
# (extend as needed)
# --------------------------------------------------
LESSON_PHONEMES = {
    35: ["AE1"],              # short a
    36: ["IH1"],              # short i
    37: ["AA1"],       # short o
    39: ["AH1"],              # short u
    40: ["EH1"],              # short e
}

# --------------------------------------------------
# Load Fry words
# --------------------------------------------------
def load_fry_words(filepath="Word Lists/1000words.txt", limit=100):
    with open(filepath, "r", encoding="utf-8") as f:
        words = [line.strip().lower() for line in f if line.strip()]
    return set(words[:limit])

# --------------------------------------------------
# Load review phonics words from spreadsheet
# --------------------------------------------------
def load_previous_phonics_words(filepath="phonics_lessons.xlsx", lesson_num=35):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[1]

    review_words = set()
    for ln in range(1, lesson_num):
        row = ws[ln + 1]
        words_raw = row[1].value
        if words_raw:
            review_words.update(
                w.strip().lower()
                for w in words_raw.split(",")
                if w.strip()
            )
    return review_words

# --------------------------------------------------
# Check phonics via pronouncing
# --------------------------------------------------
def has_target_phonics(word, target_phonemes):
    pronunciations = pronouncing.phones_for_word(word)
    for pron in pronunciations:
        for ph in target_phonemes:
            if ph in pron:
                return True
    return False

# --------------------------------------------------
# Analyze pasted story
# --------------------------------------------------
def analyze_story(story_text, lesson_num):
    words = story_text.split()
    cleaned_words = [
        w.strip(string.punctuation).lower()
        for w in words
        if w.strip(string.punctuation)
    ]

    total_words = len(cleaned_words)

    fry_limit = LESSON_FRY_LIMITS.get(lesson_num, 40)
    fry_words = load_fry_words(limit=fry_limit)
    review_words = load_previous_phonics_words(
        "phonics_lessons.xlsx", lesson_num
    )

    target_phonemes = LESSON_PHONEMES.get(lesson_num, [])

    target_count = 0
    known_count = 0
    leftover_count = 0

    for word in cleaned_words:
        if has_target_phonics(word, target_phonemes):
            target_count += 1
        elif word in fry_words or word in review_words:
            known_count += 1
        else:
            leftover_count += 1

    return {
        "total_words": total_words,
        "target_phonics_pct": (target_count / total_words) * 100 if total_words else 0,
        "fry_or_review_pct": (known_count / total_words) * 100 if total_words else 0,
        "leftover_pct": (leftover_count / total_words) * 100 if total_words else 0,
    }

# --------------------------------------------------
# COPY–PASTE USAGE
# --------------------------------------------------
if __name__ == "__main__":

    lesson_num = 37  # ← CHANGE THIS PER STORY

    story = """
    A fox and a dog are pals.  
    They like to jog at the pond.  
    One hot day, the dog got a big mop.  
    The fox did not have a job to do, so he sat on a log.  
    The dog got the mop wet in the pond.  
    But then, a pod fell on the dog!  
    The dog sobs and nods.  
    The fox hops and hops to help his pal.  
    The fox and dog blot the pod.  
    They bop and flop as they mop it up.  
    The pond is not a bog now.  
    The fox has fun and hops onto the log.  
    The dog runs to the fox.  
    The pals sit on the log and look at the pond.  
    They are glad the pond is no longer a bog.  
    The fox and the dog had a lot of fun.
    """

    results = analyze_story(story, lesson_num)

    print(f"\nUFLI Lesson {lesson_num} Analysis\n" + "-" * 30)
    for k, v in results.items():
        if "pct" in k:
            print(f"{k}: {v:.2f}%")
        else:
            print(f"{k}: {v}")

