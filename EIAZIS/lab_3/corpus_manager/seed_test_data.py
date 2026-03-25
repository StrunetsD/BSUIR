from io import BytesIO
from pathlib import Path
import argparse

from app import app, db, process_file_direct
from models import Document, Sentence, SyntaxAnalysis, Token


TESTS_DIR = Path(__file__).parent / 'tests'


def reset_database():
    db.session.query(SyntaxAnalysis).delete()
    db.session.query(Token).delete()
    db.session.query(Sentence).delete()
    db.session.query(Document).delete()
    db.session.commit()


def build_metadata(file_path):
    stem = file_path.stem.replace('test_', '').replace('_', ' ')
    title = stem.title()
    size_map = {
        'tiny': 'Short demo text',
        'simple': 'Short article',
        'medium': 'Medium analytical text',
        'long': 'Long analytical review',
        'multi': 'Structured web page',
        'dialogue': 'Dialogue sample',
        'complex': 'Complex syntax sample',
        'noise': 'Noisy HTML sample',
        'nested': 'Nested layout sample',
        'lists': 'List-oriented sample',
    }

    genre = 'English HTML test document'
    for key, value in size_map.items():
        if key in file_path.stem:
            genre = value
            break

    return {
        'title': title,
        'author': 'Seed Generator',
        'genre': genre,
        'year': 2026,
    }


def seed_documents(limit=None):
    html_files = sorted(TESTS_DIR.glob('*.html'))
    if limit:
        html_files = html_files[:limit]

    created = []
    for file_path in html_files:
        metadata = build_metadata(file_path)
        content = file_path.read_bytes()
        document, message = process_file_direct(
            BytesIO(content),
            file_path.name,
            metadata['title'],
            metadata['author'],
            metadata['genre'],
            metadata['year']
        )
        if document is None:
            raise RuntimeError(f'Failed to import {file_path.name}: {message}')
        created.append((file_path.name, message))

    return created


def main():
    parser = argparse.ArgumentParser(description='Seed lab_3 PostgreSQL database with HTML test documents.')
    parser.add_argument('--reset', action='store_true', help='Clear documents and analyses before seeding')
    parser.add_argument('--limit', type=int, default=None, help='Import only first N HTML files')
    args = parser.parse_args()

    with app.app_context():
        db.create_all()
        if args.reset:
            reset_database()

        created = seed_documents(limit=args.limit)
        print(f'Imported documents: {len(created)}')
        for file_name, message in created:
            print(f'- {file_name}: {message}')


if __name__ == '__main__':
    main()
