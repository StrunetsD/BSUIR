"""
English dependency parsing via spaCy. Falls back gracefully if the model is missing.
"""
import os
import time

# Coarse POS → human-readable (UD + common tags)
POS_LABELS = {
    'NOUN': 'noun',
    'PROPN': 'proper noun',
    'PRON': 'pronoun',
    'VERB': 'verb',
    'AUX': 'aux',
    'ADJ': 'adjective',
    'ADV': 'adverb',
    'ADP': 'adposition',
    'DET': 'determiner',
    'NUM': 'numeral',
    'CONJ': 'conjunction',
    'CCONJ': 'conjunction',
    'SCONJ': 'conjunction',
    'PART': 'particle',
    'PUNCT': 'punctuation',
    'INTJ': 'interjection',
    'X': 'other',
    'SYM': 'symbol',
    'SPACE': 'space',
}

_nlp = None
_load_error = None


def _nlp_model_name():
    return os.environ.get('SPACY_MODEL', 'en_core_web_sm')


def get_nlp():
    """Lazy-load spaCy model; returns None if unavailable."""
    global _nlp, _load_error
    if _nlp is not None:
        return _nlp
    if _load_error is not None:
        return None
    try:
        import spacy

        name = _nlp_model_name()
        _nlp = spacy.load(name)
    except Exception as exc:
        _load_error = exc
        _nlp = None
    return _nlp


def _pos_label(token):
    coarse = getattr(token, 'pos_', None) or ''
    if coarse in POS_LABELS:
        return POS_LABELS[coarse]
    tag = getattr(token, 'tag_', '') or ''
    return tag.lower().replace('-', ' ') or 'token'


def _build_nested_tree(rows):
    """rows: list of dicts with id (0-based), head_id (None for root)."""
    if not rows:
        return {}
    n = len(rows)
    children = [[] for _ in range(n)]
    root = None
    for r in rows:
        i = r['id']
        h = r.get('head_id')
        if h is None:
            root = i
        elif 0 <= h < n:
            children[h].append(i)
        else:
            root = root if root is not None else i
    if root is None:
        root = 0

    def build(i):
        r = rows[i]
        return {
            'id': i,
            'text': r['text'],
            'lemma': r.get('lemma', ''),
            'dep': r.get('dep', ''),
            'pos_label': r.get('pos_label', ''),
            'tag': r.get('tag', ''),
            'children': [build(j) for j in sorted(children[i])],
        }

    return build(root)


def build_nested_tree(rows):
    """Public wrapper for nested dependency tree JSON (0-based ids, head_id)."""
    return _build_nested_tree(rows)


def parse_dependencies_spacy(sentence_text):
    """
    Returns dict with tokens (0-based ids), parse_ms, engine, model; or None if spaCy unusable.
    """
    nlp = get_nlp()
    if nlp is None:
        return None

    t0 = time.perf_counter()
    doc = nlp(sentence_text)
    parse_ms = round((time.perf_counter() - t0) * 1000, 2)

    rows = []
    for i, t in enumerate(doc):
        is_root = t.head == t
        rows.append({
            'id': i,
            'text': t.text,
            'lemma': t.lemma_,
            'tag': t.tag_ or '',
            'pos': t.pos_ or '',
            'pos_label': _pos_label(t),
            'dep': 'root' if t.dep_ in ('ROOT', 'root') else t.dep_.lower(),
            'head_id': None if is_root else t.head.i,
        })

    return {
        'engine': 'spacy',
        'model': _nlp_model_name(),
        'parse_ms': parse_ms,
        'tokens': rows,
        'tree': _build_nested_tree(rows),
    }
