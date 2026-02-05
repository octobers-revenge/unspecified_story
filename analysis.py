import openpyxl
import pronouncing
import string
import re

VCe_PATTERN = re.compile(r"[aeiou][bcdfghjklmnpqrstvwxyz]e$")

def has_vce_ending(word):
    return bool(VCe_PATTERN.search(word))

def analyze_ture_story(story_text, lesson_num):
    words = story_text.split()
    cleaned_words = [
        w.strip(string.punctuation).lower()
        for w in words
        if w.strip(string.punctuation)
    ]

    total_words = len(cleaned_words)
    if total_words == 0:
        return {
            "ture_pct": 0,
            "fry_or_review_pct": 0,
            "leftover_pct": 0,
        }

    fry_limit = LESSON_FRY_LIMITS.get(lesson_num, 40)
    fry_words = load_fry_words(limit=fry_limit)
    review_words = load_previous_phonics_words(
        "phonics_lessons.xlsx", lesson_num
    )

    ture_count = 0
    known_count = 0
    leftover_count = 0

    for word in cleaned_words:
        # Count words that end with 'e' as "ture"
        if word.endswith("e"):
            ture_count += 1
        elif word in fry_words or word in review_words:
            known_count += 1
        else:
            leftover_count += 1

    return {
        "ture_pct": (ture_count / total_words) * 100,
        "fry_or_review_pct": (known_count / total_words) * 100,
        "leftover_pct": (leftover_count / total_words) * 100,
    }


# --------------------------------------------------
# Fry word limits by UFLI lesson
# --------------------------------------------------
LESSON_FRY_LIMITS = {
    35: 40,
    48: 60,
    60: 80,
    80: 120,
    91: 240,
    120: 240
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
    40: ["EH1"],  
    48: ["CH"],
    57: ["S"],
    80: [],
    91: ["UW1"],
    108: [],            
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

    lesson_num = 120  # ← CHANGE THIS PER STORY

    story = """
    Tom was a small boy with a big dream.  
    He wanted to build a cool treehouse.  
    On Tuesday, he got a blueprint for his plan.  
    The blueprint was new and very blue.  

    His mom came to see his plan.  
    She looked at it and smiled.  
    Tom and his mom began to gather items.  
    They found wood, nails, and a hammer. 
    
    Tom's sister, Sue, also came to help.  
    She brought some juice and fruit.  
    Tom asked, "Can I have a sip?"  
    Sue gave him juice and a big red apple. 
    
    The wind blew strong all day.  
    But they did not stop.  
    Tom and Sue took turns with the hammer.  
    Their arms got tired, but they kept on. 
    
    At last, they had built the base.  
    They were glad and took a break.  
    Tom drew a big sun on the blueprint.  
    He said, "This will be the top of the treehouse."  

    On the next day, the work began again.  
    Tom felt like it was a long cruise, not work.  
    He ate some fruit while thinking.  
    Sue said, "I will chew some gum."  

    Tom laughed and nodded.  
    After much effort, the treehouse was done.  
    It was a fine new place for fun.  
    Tom and Sue celebrated with more juice.
    """

    results = analyze_ture_story(story, lesson_num)

    print(f"\nUFLI Lesson {lesson_num} Analysis\n" + "-" * 30)
    for k, v in results.items():
        if "pct" in k:
            print(f"{k}: {v:.2f}%")
        else:
            print(f"{k}: {v}")

