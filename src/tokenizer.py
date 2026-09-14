import re

def tokenize(text: str):
    text = text.lower().strip()
    text = re.sub(r"[.!?]", "", text)
    return text.split()
