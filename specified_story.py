import os
import random
import re
from openai import OpenAI
from dotenv import load_dotenv
import pronouncing

load_dotenv()
client = OpenAI()

OUTPUT_DIR = "generated_student_stories"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# GPT-friendly phonics descriptions
phonics_patterns = [
    "m /m/ (the 'm' sound as in mat)",
    "t /t/ (the 't' sound as in tap)",
    "g /g/ (the 'g' sound as in go)",
    "o /ŏ/ (short o sound as in hot)",
    "u /ŭ/ (short u sound as in cup)"
]

def clean_text(text):
    return re.sub(r'[^a-zA-Z\s]', '', text.lower()).split()

def word_matches_pattern(word, pattern):
    word = word.lower()
    phones = pronouncing.phones_for_word(word)
    if not phones:
        return False
    # Check letter AND phoneme for visual decodability
    if pattern.startswith("m"):
        return "m" in word and any("M" in p for p in phones)
    elif pattern.startswith("t"):
        return "t" in word and any("T" in p for p in phones)
    elif pattern.startswith("g"):
        return "g" in word and any("G" in p for p in phones)
    elif pattern.startswith("o"):
        return "o" in word and any("AA1" in p for p in phones)
    elif pattern.startswith("u"):
        return "u" in word and any("AH1" in p for p in phones)
    return False

def calculate_decodable_score(story_text, phonics_pattern):
    words = clean_text(story_text)
    if not words:
        return 0.0
    matches = sum(word_matches_pattern(w, phonics_pattern) for w in words)
    return matches / len(words)

def calculate_diversity_score(story_text):
    words = clean_text(story_text)
    if not words:
        return 0.0
    unique_count = len(set(words))
    return unique_count / len(words)

def generate_decodable_story(student_profile, phonics_pattern, num_pages=5):
    prompt = f"""
Create a decodable text for a grade {student_profile['grade']} student aged {student_profile['age']}:

- Focus on the phonics pattern: {phonics_pattern}
- Include at least 10 words with this phonics pattern
- Do not use multisyllabic or complex words
- Use high-frequency words naturally
- Have a clear problem, events, and solution
- Use "{student_profile['name']}" as the main character
- All other character names should follow the phonics pattern
- The story should primarily be about: {student_profile['interests']}
- Attend to {student_profile['ethnicity']} cultural context in names or setting
- Sentences should be simple and repetitive, 5-8 words per sentence
- The story should have {num_pages} pages, each separated by '---'
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def main():
    student_profiles = [
        {"id": "1", "name": "Emma Johnson", "age": 5, "grade": "K", "interests": "Reading fairytales", "ethnicity": "Caucasian"},
        {"id": "2", "name": "Liam Chen", "age": 6, "grade": "1", "interests": "Science fiction stories", "ethnicity": "Chinese/Asian"},
        {"id": "5", "name": "Aisha Patel", "age": 8, "grade": "2", "interests": "Sports and fitness", "ethnicity": "South Asian/Indian"},
    ]

    for student in student_profiles:
        student_dir = os.path.join(OUTPUT_DIR, f"{student['name'].replace(' ', '_')}")
        os.makedirs(student_dir, exist_ok=True)

        for i, phonics_pattern in enumerate(phonics_patterns, start=1):
            print(f"Generating story {i} for {student['name']} (Grade {student['grade']}), pattern: {phonics_pattern}")

            story_text = generate_decodable_story(student, phonics_pattern)

            decodable_score = calculate_decodable_score(story_text, phonics_pattern)
            diversity_score = calculate_diversity_score(story_text)

            story_file = os.path.join(student_dir, f"story_{i}.txt")
            with open(story_file, "w", encoding="utf-8") as f:
                f.write(f"Phonics Pattern: {phonics_pattern}\n\n")
                f.write(story_text + "\n\n")
                f.write(f"Decodable Score: {decodable_score:.2f}\n")
                f.write(f"Diversity Score: {diversity_score:.2f}\n")

            print(f"Saved story {i} for {student['name']} with decodable score {decodable_score:.2f} and diversity score {diversity_score:.2f}.\n")

if __name__ == "__main__":
    main()

