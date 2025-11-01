import re

import pymorphy3

morph = pymorphy3.MorphAnalyzer()

TOKEN_RE = re.compile(r"[а-яё]+", re.IGNORECASE)


def normalize_text(text: str) -> set[str]:
    """
    Возвращает набор нормализованных слов из текста (леммы, нижний регистр)
    """
    tokens = TOKEN_RE.findall(text)
    lemmas = set()
    for t in tokens:
        parsed = morph.parse(t)
        if parsed:
            lemmas.add(parsed[0].normal_form.lower())
    return lemmas