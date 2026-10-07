"""Rough syllable counts for Gujarati and English text (speech-duration estimates)."""
import re

GU_CONS = re.compile(r'[\u0A95-\u0AB9\u0AF9]')        # consonants
GU_VOW  = re.compile(r'[\u0A85-\u0A94\u0AE0\u0AE1]')  # independent vowels
VIRAMA = '\u0ACD'
def syllables(text):
    n = 0
    for w in re.findall(r'[\u0A80-\u0AFF\u200c\u200d]+|[A-Za-z]+|\d+', text):
        if re.match(r'[A-Za-z]', w):
            if w.isupper() and len(w) <= 4:              # CA, BHK, PHD -> spelled letters
                n += len(w)                               # each letter ~1 syllable
            else:
                v = re.findall(r'[aeiouy]+', w.lower())
                k = len(v) - (1 if w.lower().endswith('e') and len(v) > 1 and not w.lower().endswith(('le', 'ee')) else 0)
                n += max(1, k)
        elif w.isdigit():
            n += 2 * len(w)                               # numbers read as words
        else:
            cons = len(GU_CONS.findall(w)) - w.count(VIRAMA)   # conjuncts count once
            n += max(1, cons + len(GU_VOW.findall(w)))
    return n
