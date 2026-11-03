"""Utility module for extractive summarization and keyword extraction.
No external APIs are required – everything runs locally.
"""
import re
from collections import Counter
from typing import List, Dict

# a minimal stop‑word list; you can extend it later
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was",
    "were", "has", "have", "had", "but", "not", "you", "your", "their",
    "they", "them", "its", "our", "out", "about", "which", "when", "where",
    "how", "who", "whom", "can", "could", "should", "would", "may", "might",
    "will", "into", "over", "under", "between", "after", "before", "than",
    "such", "any", "all", "most", "some", "few", "more", "other", "only",
    "also", "these", "those", "because", "while", "then", "just",
}

def _clean_text(text: str) -> str:
    """Normalize whitespace and strip markdown symbols that would distort analysis."""
    # Collapse multiple spaces and remove leading/trailing whitespace
    text = re.sub(r"\s+", " ", text.strip())
    # Remove common markdown symbols to improve language processing
    text = re.sub(r"[#>*\-\[\]\(\)\`]+", " ", text)
    return text

def summarize_text(text: str, sentence_count: int = 3) -> str:
    """Extract an *extractive* summary from ``text``.

    The algorithm:
    1. Split the text into sentences (using punctuation delimiters).
    2. Score each sentence by the frequency of its non‑stop‑word tokens.
    3. Pick the ``sentence_count`` highest‑scoring sentences.
    4. Return them **in the original order**.

    If the input is empty or contains fewer than ``sentence_count`` sentences,
    the function returns the original (truncated) text.
    """
    clean = _clean_text(text)
    if not clean:
        return ""

    # split on . ! ? followed by whitespace or end‑of‑string
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    # discard very short fragments that are unlikely to be real sentences
    sentences = [s for s in sentences if len(s.split()) >= 4]
    if not sentences:
        return clean[:500]
    if len(sentences) <= sentence_count:
        return " ".join(sentences)

    # word frequencies (ignore stop‑words)
    words = re.findall(r"\b[a-zA-Z][a-zA-Z'-]{2,}\b", clean.lower())
    freq = Counter(w for w in words if w not in STOPWORDS)
    if not freq:
        # fallback – just return the first N sentences
        return " ".join(sentences[:sentence_count])
    max_freq = max(freq.values())

    # score sentences
    scored = []
    for idx, sent in enumerate(sentences):
        sent_words = re.findall(r"\b[a-zA-Z][a-zA-Z'-]{2,}\b", sent.lower())
        # sum of normalized frequencies
        score = sum(freq[w] / max_freq for w in sent_words if w not in STOPWORDS)
        # slightly penalise very long sentences to favour concision
        score /= max(len(sent_words) ** 0.5, 1)
        scored.append((idx, score, sent))

    # keep top N, then restore original order
    top = sorted(scored, key=lambda x: x[1], reverse=True)[:sentence_count]
    top_sorted = sorted(top, key=lambda x: x[0])
    return " ".join(s for _, _, s in top_sorted)

def extract_keywords(text: str, top_n: int = 10) -> List[Dict[str, int]]:
    """Return the ``top_n`` most frequent meaningful words.

    The function:
    * lower‑cases the text,
    * extracts alphabetic tokens of length >=3,
    * removes stop‑words,
    * counts occurrences and returns a list of ``{"keyword": word, "count": cnt}``.
    If no words survive filtering, an empty list is returned.
    """
    clean = _clean_text(text)
    if not clean:
        return []
    words = re.findall(r"\b[a-zA-Z][a-zA-Z'-]{2,}\b", clean.lower())
    words = [w for w in words if w not in STOPWORDS]
    if not words:
        return []
    counts = Counter(words)
    return [{"keyword": w, "count": c} for w, c in counts.most_common(top_n)]
