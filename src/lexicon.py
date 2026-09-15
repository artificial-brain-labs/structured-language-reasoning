import json


class Lexicon:
    def __init__(self, path="knowledge/lexicon.json"):
        with open(path, "r", encoding="utf-8") as f:
            self.words = json.load(f)

    def get(self, word):
        return self.words.get(word)

    def concept(self, word):
        entry = self.get(word)
        return entry.get("concept") if entry else None

    def pos(self, word):
        entry = self.get(word)
        return entry.get("pos") if entry else None

    def feature(self, word, name):
        entry = self.get(word)
        return entry.get(name) if entry else None

    def contains(self, word):
        return word in self.words
