from models import db, Document, Sentence, Token
from sqlalchemy import func, desc
from collections import Counter
import re

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
    ).join(Sentence, Sentence.doc_id == Document.id)\
     .join(Token, Token.sentence_id == Sentence.id)\
     .filter(Token.word == word)\
     .group_by(Document.id, Document.title, Document.author)\
     .order_by(desc('cnt'))\
     .limit(10)\
     .all()
    
    pos_stats = db.session.query(
        Token.pos,
        func.count(Token.id).label('cnt')
    ).filter(Token.word == word)\
     .group_by(Token.pos)\
     .all()
    
    return {
        'word': word,
        'total': total,
        'by_doc': by_doc,
        'pos_stats': pos_stats
    }

def get_concordance_for_template(word, limit=3):
    from corpus_service import get_concordance as gc
    return gc(word, limit=limit)

def get_lemma_stats(lemma):
    lemma = lemma.lower()
    forms = db.session.query(
        Token.word,
        func.count(Token.id).label('cnt')
    ).filter(Token.lemma == lemma)\
     .group_by(Token.word)\
     .order_by(desc('cnt'))\
     .all()
    
    total = sum(cnt for _, cnt in forms)
    
    pos_stats = db.session.query(
        Token.pos,
        func.count(Token.id).label('cnt')
    ).filter(Token.lemma == lemma)\
     .group_by(Token.pos)\
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
    
    top_wordforms = db.session.query(
        Token.word,
        func.count(Token.id).label('cnt')
    ).group_by(Token.word)\
     .order_by(desc('cnt'))\
     .limit(10)\
     .all()
    
    top_lemmas = db.session.query(
        Token.lemma,
        func.count(Token.id).label('cnt')
    ).filter(Token.lemma != None)\
     .group_by(Token.lemma)\
     .order_by(desc('cnt'))\
     .limit(10)\
     .all()
    
    pos_distribution = db.session.query(
        Token.pos,
        func.count(Token.id).label('cnt')
    ).group_by(Token.pos)\
     .order_by(desc('cnt'))\
     .all()
    
    unique_words = db.session.query(func.count(func.distinct(Token.word))).scalar()
    unique_lemmas = db.session.query(func.count(func.distinct(Token.lemma))).scalar()
    
    author_stats = db.session.query(
        Document.author,
        func.count(Document.id).label('doc_cnt'),
        func.sum(func.length(Document.title)).label('approx_size')
    ).group_by(Document.author)\
     .order_by(desc('doc_cnt'))\
     .limit(5)\
     .all()
    
    return {
        'total_docs': total_docs,
        'total_sents': total_sents,
        'total_tokens': total_tokens,
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
    except Exception as e:
        print(f"Ошибка в filter_by_pos: {e}")
        return []

def get_ngrams(n=2, min_freq=2):
    return [("пример биграммы", 5), ("другая биграмма", 3)]