import re

import pymorphy3

morph = pymorphy3.MorphAnalyzer()

TOKEN_RE = re.compile(r"[а-яё]+", re.IGNORECASE)


def normalize_text(text: str) -> set[str]:
    """
    Normalizes text by tokenizing, lemmatizing, and converting to lowercase.

    This function takes a string of text, extracts Russian words, converts them to their
    base form (lemmatization), and returns a set of unique normalized tokens.

    :param text: Input text to be normalized
    :type text: str
    :return: Set of normalized word lemmas in lowercase
    :rtype: set[str]
    :example:
        >>> normalize_text("Быстрый коричневый лис")
        {'быстрый', 'коричневый', 'лиса'}
    """
    tokens = TOKEN_RE.findall(text)
    lemmas = set()
    for t in tokens:
        parsed = morph.parse(t)
        if parsed:
            lemmas.add(parsed[0].normal_form.lower())
    return lemmas