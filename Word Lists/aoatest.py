import openpyxl
import re

def count_syllables(word: str) -> int:
    """Approximate syllable count by counting groups of vowels."""
    word = word.lower()
    vowels = re.findall(r"[aeiouy]+", word)
    return max(1, len(vowels))

def load_aoa_words(filepath="AoA_ratings_Kuperman_et_al_BRM.xlsx"):
    """Load all AoA words, filter for readability, and keep AoA value."""
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[0]

    words = []
    for row in ws.iter_rows(min_row=2, max_col=5):
        word = row[0].value
        val = row[4].value
        if isinstance(word, str) and isinstance(val, (int, float)):
            words.append((word.strip().lower(), val))

    words.sort(key=lambda x: x[1])  # sort by AoA

    filtered = []
    for w, v in words:
        if count_syllables(w) > 1:
            continue
        if len(w) > 6:
            continue
        if not w.isalpha():
            continue
        filtered.append((w, v))

    return filtered

def save_split_by_grade(words):
    """Save words into 3 files by AoA: K, Grade 1, Grade 2."""
    k_words = [w for w, v in words if v < 5]
    g1_words = [w for w, v in words if 5 <= v < 6]
    g2_words = [w for w, v in words if 6 <= v < 7]

    with open("kindergartenAOA.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(k_words))
    with open("grade1AOA.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(g1_words))
    with open("grade2AOA.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(g2_words))

    print(f"Saved {len(k_words)} K words, {len(g1_words)} Grade 1 words, {len(g2_words)} Grade 2 words.")

def main():
    aoa_words = load_aoa_words()
    save_split_by_grade(aoa_words)

if __name__ == "__main__":
    main()