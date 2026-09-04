from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(200))
    year = db.Column(db.Integer)
    genre = db.Column(db.String(100))
    file_path = db.Column(db.String(500))
    source_format = db.Column(db.String(20))
    text_content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sentences = db.relationship('Sentence', backref='document', lazy='dynamic', 
                                cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Document {self.title}>'

class Sentence(db.Model):
    __tablename__ = 'sentences'
    
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), 
                       nullable=False)
    text = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer)
    
    tokens = db.relationship('Token', backref='sentence', lazy='dynamic',
                             cascade='all, delete-orphan')
    syntax_analysis = db.relationship(
        'SyntaxAnalysis',
        backref='sentence',
        uselist=False,
        cascade='all, delete-orphan'
    )
    
    __table_args__ = (
        db.Index('idx_sentences_doc_id', 'doc_id'),
        db.Index('idx_sentences_doc_id_position', 'doc_id', 'position'),
    )

class Token(db.Model):
    __tablename__ = 'tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentences.id', ondelete='CASCADE'),
                            nullable=False)
    word = db.Column(db.String(100), nullable=False)
    lemma = db.Column(db.String(100))
    pos = db.Column(db.String(50))
    grammemes = db.Column(db.String(200))
    position = db.Column(db.Integer)
    
    __table_args__ = (
        db.Index('idx_tokens_word', 'word'),
        db.Index('idx_tokens_lemma', 'lemma'),
        db.Index('idx_tokens_pos', 'pos'),
        db.Index('idx_tokens_sentence_id', 'sentence_id'),
        db.Index('idx_tokens_sentence_id_pos', 'sentence_id', 'position'),
    )


class SyntaxAnalysis(db.Model):
    __tablename__ = 'syntax_analyses'

    id = db.Column(db.Integer, primary_key=True)
    sentence_id = db.Column(
        db.Integer,
        db.ForeignKey('sentences.id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )
    summary = db.Column(db.Text, nullable=False)
    tree_view = db.Column(db.Text)
    payload_json = db.Column(db.Text)
    notes = db.Column(db.Text)
    edited_summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
