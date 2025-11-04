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


def clean_description(description: str) -> str:
    """
    Clean the description by removing HTML tags and extra whitespace.

    :param description: Input description to be cleaned
    :type description: str
    :return: Cleaned description
    :rtype: str
    """
    cleaned_text = description.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')

    # Добавляем пробелы после точек, если следующая буква
    result = []
    for i, char in enumerate(cleaned_text):
        result.append(char)
        if char == '.' and i + 1 < len(cleaned_text) and cleaned_text[i + 1].isalpha():
            result.append(' ')

    cleaned_text = ''.join(result)

    # Убираем лишние пробелы
    while '  ' in cleaned_text:
        cleaned_text = cleaned_text.replace('  ', ' ')

    if cleaned_text.startswith('Описание'):
        cleaned_text = cleaned_text[8:]
    else:
        cleaned_text = cleaned_text

    return cleaned_text