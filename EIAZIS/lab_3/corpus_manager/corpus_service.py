import json
from collections import Counter

import nltk
from nltk import RegexpParser, pos_tag
from nltk.stem import WordNetLemmatizer
from sqlalchemy import desc, func

from models import Document, Sentence, SyntaxAnalysis, Token, db
from syntax_parser import build_nested_tree, parse_dependencies_spacy

lemmatizer = WordNetLemmatizer()

CHUNK_GRAMMAR = r"""
    NP: {<DT>?<JJ.*>*<NN.*>+}
    PP: {<IN><NP>}
    VP: {<MD>?<VB.*><RB.?>*<VB.*>*<NP|PP>*}
"""

POS_EXAMPLES = {
    'NN': 'noun',
    'NNS': 'plural noun',
    'NNP': 'proper noun',
    'VB': 'verb',
    'VBD': 'verb, past tense',
    'VBG': 'verb, gerund',
    'VBN': 'verb, past participle',
    'VBP': 'verb, present',
    'VBZ': 'verb, 3rd person',
    'JJ': 'adjective',
    'RB': 'adverb',
    'IN': 'preposition',
}


def search_words(query, search_type='word'):
    query = query.lower().strip()

    if search_type == 'word':
        tokens = Token.query.filter(Token.word == query).limit(200).all()
    elif search_type == 'lemma':
        tokens = Token.query.filter(Token.lemma == query).limit(200).all()
    elif search_type == 'pos':
        tokens = Token.query.filter(Token.pos == query.upper()).limit(200).all()
    else:
        tokens = []

    results = []
    for token in tokens:
        results.append({
            'id': token.id,
            'word': token.word,
            'lemma': token.lemma,
            'pos': token.pos,
            'grammemes': token.grammemes,
            'sentence_text': token.sentence.text[:200] + '...' if len(token.sentence.text) > 200 else token.sentence.text,
            'doc_title': token.sentence.document.title,
            'doc_id': token.sentence.document.id,
            'doc_author': token.sentence.document.author
        })

    return results


def get_concordance(word, context_size=5, limit=50):
    tokens = Token.query.filter(Token.word == word.lower()).limit(limit).all()

    lines = []
    for token in tokens:
        sent = token.sentence

        left_tokens = Token.query.filter(
            Token.sentence_id == sent.id,
            Token.position < token.position
        ).order_by(Token.position).limit(context_size).all()

        right_tokens = Token.query.filter(
            Token.sentence_id == sent.id,
            Token.position > token.position
        ).order_by(Token.position).limit(context_size).all()

        left_text = ' '.join([t.word for t in left_tokens])
        right_text = ' '.join([t.word for t in right_tokens])

        lines.append({
            'left': left_text,
            'word': token.word.upper(),
            'right': right_text,
            'doc_title': sent.document.title,
            'doc_id': sent.document.id,
            'doc_author': sent.document.author
        })

    return lines


def get_word_stats(word):
    word = word.lower()

    total = Token.query.filter(Token.word == word).count()

    by_doc = db.session.query(
        Document.title,
        Document.author,
        func.count(Token.id).label('cnt')
    ).join(Sentence, Sentence.doc_id == Document.id) \
        .join(Token, Token.sentence_id == Sentence.id) \
        .filter(Token.word == word) \
        .group_by(Document.id, Document.title, Document.author) \
        .order_by(desc('cnt')) \
        .limit(10) \
        .all()

    pos_stats = db.session.query(
        Token.pos,
        func.count(Token.id).label('cnt')
    ).filter(Token.word == word) \
        .group_by(Token.pos) \
        .all()

    return {
        'word': word,
        'total': total,
        'by_doc': by_doc,
        'pos_stats': pos_stats
    }


def get_lemma_stats(lemma):
    lemma = lemma.lower()
    forms = db.session.query(
        Token.word,
        func.count(Token.id).label('cnt')
    ).filter(Token.lemma == lemma) \
        .group_by(Token.word) \
        .order_by(desc('cnt')) \
        .all()

    total = sum(cnt for _, cnt in forms)

    pos_stats = db.session.query(
        Token.pos,
        func.count(Token.id).label('cnt')
    ).filter(Token.lemma == lemma) \
        .group_by(Token.pos) \
        .all()

    return {
        'lemma': lemma,
        'total': total,
        'forms': forms,
        'pos_stats': pos_stats
    }


def get_corpus_stats():
    total_docs = Document.query.count()
    total_sents = Sentence.query.count()
    total_tokens = Token.query.count()
    total_syntax = SyntaxAnalysis.query.count()

    top_wordforms = db.session.query(
        Token.word,
        func.count(Token.id).label('cnt')
    ).group_by(Token.word) \
        .order_by(desc('cnt')) \
        .limit(10) \
        .all()

    top_lemmas = db.session.query(
        Token.lemma,
        func.count(Token.id).label('cnt')
    ).filter(Token.lemma.isnot(None)) \
        .group_by(Token.lemma) \
        .order_by(desc('cnt')) \
        .limit(10) \
        .all()

    pos_distribution = db.session.query(
        Token.pos,
        func.count(Token.id).label('cnt')
    ).group_by(Token.pos) \
        .order_by(desc('cnt')) \
        .all()

    unique_words = db.session.query(func.count(func.distinct(Token.word))).scalar()
    unique_lemmas = db.session.query(func.count(func.distinct(Token.lemma))).scalar()

    author_stats = db.session.query(
        Document.author,
        func.count(Document.id).label('doc_cnt'),
        func.sum(func.length(Document.title)).label('approx_size')
    ).group_by(Document.author) \
        .order_by(desc('doc_cnt')) \
        .limit(5) \
        .all()

    return {
        'total_docs': total_docs,
        'total_sents': total_sents,
        'total_tokens': total_tokens,
        'total_syntax': total_syntax,
        'unique_words': unique_words,
        'unique_lemmas': unique_lemmas,
        'top_wordforms': top_wordforms,
        'top_lemmas': top_lemmas,
        'pos_distribution': pos_distribution,
        'author_stats': author_stats
    }


def get_document(doc_id):
    return Document.query.get_or_404(doc_id)


def get_documents_list():
    return Document.query.order_by(Document.title).all()


def filter_by_pos(pos, limit=100):
    try:
        pos = pos.upper()
        tokens = Token.query.filter(Token.pos == pos).limit(limit).all()

        results = []
        for token in tokens:
            sentence_text = token.sentence.text
            if len(sentence_text) > 150:
                sentence_text = sentence_text[:150] + '...'

            results.append({
                'word': token.word,
                'lemma': token.lemma,
                'sentence': sentence_text,
                'doc_id': token.sentence.document.id,
                'doc_title': token.sentence.document.title
            })

        return results
    except Exception as exc:
        print(f'Error in filter_by_pos: {exc}')
        return []


def get_ngrams(n=2, min_freq=2):
    words = [token.word for token in Token.query.order_by(Token.id).limit(5000).all()]
    ngrams = Counter(tuple(words[i:i + n]) for i in range(len(words) - n + 1))
    return [(' '.join(key), value) for key, value in ngrams.items() if value >= min_freq][:10]


def _build_chunk_tree(sentence_text):
    tokens = nltk.word_tokenize(sentence_text)
    tagged_tokens = pos_tag(tokens)
    parser = RegexpParser(CHUNK_GRAMMAR)
    tree = parser.parse(tagged_tokens)
    return tokens, tagged_tokens, tree


def _extract_phrases(tree, label):
    phrases = []
    for subtree in tree.subtrees(lambda current: current.label() == label):
        phrases.append(' '.join(word for word, _ in subtree.leaves()))
    return phrases


def _pick_subject(noun_phrases, predicate):
    if not noun_phrases:
        return None
    if not predicate:
        return noun_phrases[0]

    predicate_words = predicate.split()
    predicate_anchor = predicate_words[0] if predicate_words else None
    for phrase in noun_phrases:
        if predicate_anchor and phrase in predicate:
            continue
        return phrase
    return noun_phrases[0]


def _spacy_rows_to_legacy(spacy_tokens):
    """1-based ids and head indices for compatibility with older exports."""
    legacy = []
    for r in spacy_tokens:
        hid = r['head_id']
        legacy.append({
            'id': r['id'] + 1,
            'text': r['text'],
            'lemma': r['lemma'],
            'pos': r['tag'] or r['pos'],
            'relation': r['dep'],
            'head': None if hid is None else hid + 1,
        })
    return legacy


def _build_dependency_like_rows(tagged_tokens, predicate_word):
    rows = []
    predicate_index = None
    if predicate_word:
        for idx, (word, _) in enumerate(tagged_tokens, start=1):
            if word == predicate_word:
                predicate_index = idx
                break

    for idx, (word, pos) in enumerate(tagged_tokens, start=1):
        relation = 'dep'
        head = predicate_index

        if predicate_index and idx == predicate_index:
            relation = 'root'
            head = None
        elif pos.startswith('NN'):
            relation = 'nsubj' if predicate_index and idx < predicate_index else 'obj'
        elif pos.startswith('JJ'):
            relation = 'amod'
        elif pos.startswith('RB'):
            relation = 'advmod'
        elif pos == 'IN':
            relation = 'prep'
        elif pos.startswith('VB'):
            relation = 'xcomp'
        elif pos in {'DT', 'PRP$', 'POS'}:
            relation = 'det'

        rows.append({
            'id': idx,
            'text': word,
            'lemma': lemmatizer.lemmatize(word.lower(), 'v' if pos.startswith('VB') else 'n'),
            'pos': pos,
            'relation': relation,
            'head': head
        })

    return rows


def _format_dep_tree_lines(dependency_rows, id_to_text):
    lines = []
    for row in dependency_rows:
        rel = row['relation']
        h = row.get('head')
        if rel == 'root':
            head_show = 'ROOT'
        elif h is not None:
            head_show = id_to_text.get(h, str(h))
        else:
            head_show = '-'
        lines.append(
            f"{row['id']:>2}. {row['text']:<18} [{row['pos']}] --{rel}--> {head_show}"
        )
    return lines


def analyze_sentence_syntax(sentence_text):
    tokens, tagged_tokens, tree = _build_chunk_tree(sentence_text)
    noun_phrases = _extract_phrases(tree, 'NP')
    verb_phrases = _extract_phrases(tree, 'VP')
    prep_phrases = _extract_phrases(tree, 'PP')

    predicate = verb_phrases[0] if verb_phrases else next(
        (word for word, pos in tagged_tokens if pos.startswith('VB')),
        None
    )
    subject = _pick_subject(noun_phrases, predicate)

    spacy_result = parse_dependencies_spacy(sentence_text)
    if spacy_result:
        dependency_rows = _spacy_rows_to_legacy(spacy_result['tokens'])
        id_to_text = {row['id']: row['text'] for row in dependency_rows}
        dependency_parse = {
            'engine': spacy_result['engine'],
            'model': spacy_result['model'],
            'parse_ms': spacy_result['parse_ms'],
            'tokens': spacy_result['tokens'],
            'tree': spacy_result['tree'],
        }
    else:
        dependency_rows = _build_dependency_like_rows(
            tagged_tokens, predicate.split()[0] if predicate else None
        )
        id_to_text = {row['id']: row['text'] for row in dependency_rows}
        heuristic_tokens = [
            {
                'id': row['id'] - 1,
                'text': row['text'],
                'lemma': row['lemma'],
                'tag': row['pos'],
                'pos': '',
                'pos_label': POS_EXAMPLES.get(row['pos'], row['pos']),
                'dep': row['relation'],
                'head_id': None
                if row['relation'] == 'root'
                else (row['head'] - 1 if row['head'] else None),
            }
            for row in dependency_rows
        ]
        dependency_parse = {
            'engine': 'nltk_heuristic',
            'model': None,
            'parse_ms': None,
            'tokens': heuristic_tokens,
            'tree': build_nested_tree(heuristic_tokens),
        }

    summary = '\n'.join([
        f"Clause core: subject - {subject or 'not found'}; predicate - {predicate or 'not found'}.",
        f"Noun phrases: {', '.join(noun_phrases) if noun_phrases else 'not found'}.",
        f"Verb phrases: {', '.join(verb_phrases) if verb_phrases else 'not found'}.",
        f"Prepositional phrases: {', '.join(prep_phrases) if prep_phrases else 'not found'}.",
    ])
    if dependency_parse.get('parse_ms') is not None:
        summary += (
            f"\nDependency parse: {dependency_parse['engine']} "
            f"({dependency_parse.get('model', '')}) in {dependency_parse['parse_ms']} ms."
        )

    tree_lines = _format_dep_tree_lines(dependency_rows, id_to_text)

    tagged_for_table = []
    if spacy_result:
        for t in spacy_result['tokens']:
            tagged_for_table.append({
                'word': t['text'],
                'pos': t['tag'] or t['pos'],
                'label': t['pos_label'],
            })
    else:
        tagged_for_table = [
            {'word': word, 'pos': pos, 'label': POS_EXAMPLES.get(pos, pos)}
            for word, pos in tagged_tokens
        ]

    payload = {
        'sentence': sentence_text,
        'tokens': tokens,
        'tagged_tokens': tagged_for_table,
        'subject': subject,
        'predicate': predicate,
        'noun_phrases': noun_phrases,
        'verb_phrases': verb_phrases,
        'prepositional_phrases': prep_phrases,
        'chunk_tree': tree.pformat(margin=100),
        'dependencies': dependency_rows,
        'dependency_parse': dependency_parse,
    }

    return {
        'summary': summary,
        'tree_view': '\n'.join(tree_lines) + '\n\nChunk tree:\n' + tree.pformat(margin=100),
        'payload_json': json.dumps(payload, ensure_ascii=False, indent=2),
    }


def build_document_syntax_analyses(doc_id, force=False):
    document = get_document(doc_id)
    analyses = []

    for sentence in document.sentences.order_by(Sentence.position).all():
        if sentence.syntax_analysis and not force:
            analyses.append(sentence.syntax_analysis)
            continue

        result = analyze_sentence_syntax(sentence.text)
        analysis = sentence.syntax_analysis
        if analysis is None:
            analysis = SyntaxAnalysis(sentence_id=sentence.id, **result)
            db.session.add(analysis)
        else:
            analysis.summary = result['summary']
            analysis.tree_view = result['tree_view']
            analysis.payload_json = result['payload_json']
        analyses.append(analysis)

    db.session.commit()
    return analyses


def get_document_syntax_data(doc_id):
    document = get_document(doc_id)
    analyses = build_document_syntax_analyses(doc_id)
    return document, analyses


def get_syntax_analysis(analysis_id):
    return SyntaxAnalysis.query.get_or_404(analysis_id)


def update_syntax_analysis(analysis_id, edited_summary, notes):
    analysis = get_syntax_analysis(analysis_id)
    analysis.edited_summary = edited_summary.strip() if edited_summary and edited_summary.strip() else None
    analysis.notes = notes.strip() if notes and notes.strip() else None
    db.session.commit()
    return analysis


def export_syntax_report(doc_id):
    document, analyses = get_document_syntax_data(doc_id)
    report = {
        'document': {
            'id': document.id,
            'title': document.title,
            'author': document.author,
            'genre': document.genre,
            'year': document.year,
            'source_format': document.source_format
        },
        'analyses': []
    }

    for analysis in analyses:
        payload = json.loads(analysis.payload_json) if analysis.payload_json else {}
        report['analyses'].append({
            'sentence_id': analysis.sentence_id,
            'sentence_position': analysis.sentence.position,
            'sentence_text': analysis.sentence.text,
            'summary': analysis.edited_summary or analysis.summary,
            'notes': analysis.notes,
            'tree_view': analysis.tree_view,
            'payload': payload
        })

    return report
