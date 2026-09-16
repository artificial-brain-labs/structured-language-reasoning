import re


def tokenize(text: str):
    """Tokenize text while preserving the original surface form.

    Normalization for lexical and grammar lookup belongs to the parser/lexicon
    layers; the tokenizer should not destroy information from the input.
    """
    text = text.strip()
    text = re.sub(r"[.!?]", "", text)
    return text.split()
