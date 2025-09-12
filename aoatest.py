import openpyxl
import re

def count_syllables(word: str) -> int:
    """Approximate syllable count by counting groups of vowels."""
    word = word.lower()
    vowels = re.findall(r"[aeiouy]+", word)
    return max(1, len(vowels))

def load_fry_words(filepath="1000words.txt", n=100):
    """Load top n Fry words from text file (assume one word per line)."""
    fry_words = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()
            if word:
                fry_words.append(word)
    return fry_words[:n]

def lowest_n_aoa_words(filepath="AoA_ratings_Kuperman_et_al_BRM.xlsx", n=300):
    """Get lowest n AoA words, filtered by readability."""
    wb = openpyxl.load_workbook(filepath)
    ws = wb.worksheets[0]

    words = []
    for row in ws.iter_rows(min_row=2, max_col=5):  
        word = row[0].value
        val = row[4].value
        if isinstance(word, str) and isinstance(val, (int, float)):
            words.append((word.strip().lower(), val))

    words.sort(key=lambda x: x[1])  # sort by AoA
    selected = words[:n]

    filtered = []
    for w, v in selected:
        syllables = count_syllables(w)
        if syllables > 1:
            continue  # only one syllable
        if len(w) > 6:
            continue
        if not w.isalpha():
            continue
        filtered.append((w, v))

    # return only the words
    return [w for w, _ in filtered]

def combined_word_list(aoa_file="AoA_ratings_Kuperman_et_al_BRM.xlsx",
                       fry_file="1000words.txt",
                       aoa_n=300, fry_n=100):
    fry_words = load_fry_words(fry_file, fry_n)
    aoa_words = lowest_n_aoa_words(aoa_file, aoa_n)

    combined = list(dict.fromkeys(fry_words + aoa_words))  # preserve order, remove duplicates

    for w in combined:
        print(w)
    print("Total combined words:", len(combined))
    return combined

def main():
    combined_word_list()

if __name__ == "__main__":
    main()