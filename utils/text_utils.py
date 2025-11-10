"""
Utility functions for text processing.
"""
import pymorphy3

morph = pymorphy3.MorphAnalyzer()

def normalize_text(text):
    """Normalize text by converting to lowercase and lemmatizing words."""
    words = text.lower().split()
    return [morph.parse(w)[0].normal_form for w in words]




