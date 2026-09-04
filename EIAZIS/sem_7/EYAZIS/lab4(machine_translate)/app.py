from flask import Flask, render_template, request, jsonify, flash
from nltk.tokenize import sent_tokenize
from translation_engine import AdvancedTranslator

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

translator = AdvancedTranslator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/translate', methods=['POST'])
def translate():
    english_text = request.form.get('english_text', '').strip()

    if not english_text:
        flash('Please enter some text to translate.', 'warning')
        return render_template('index.html')

    try:
        translation_result = translator.translate_with_stats(english_text)

        if translation_result.get('error'):
            flash(f'Translation error: {translation_result["translation"]}', 'danger')
            return render_template('index.html')

        grammatical_info = translator.get_grammatical_info(english_text)
        frequency_list = translator.get_frequency_list(english_text, grammatical_info)
        sentences = sent_tokenize(english_text)

        return render_template('index.html',
                               translation_result=translation_result,
                               grammatical_info=grammatical_info,
                               frequency_list=frequency_list,
                               sentences=sentences)

    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return render_template('index.html')

@app.route('/syntax_tree', methods=['POST'])
def syntax_tree():
    english_text = request.form.get('english_text', '').strip()
    selected_sentence = request.form.get('selected_sentence', '').strip()

    if not selected_sentence:
        flash('Please select a sentence for syntax tree generation.', 'warning')
        return render_template('index.html')

    try:
        syntax_tree_result = translator.get_syntax_tree(selected_sentence)
        translation_result = translator.translate_with_stats(english_text)
        grammatical_info = translator.get_grammatical_info(english_text)
        frequency_list = translator.get_frequency_list(english_text, grammatical_info)
        sentences = sent_tokenize(english_text)

        return render_template('index.html',
                               translation_result=translation_result,
                               grammatical_info=grammatical_info,
                               frequency_list=frequency_list,
                               sentences=sentences,
                               syntax_tree=syntax_tree_result,
                               selected_sentence=selected_sentence)

    except Exception as e:
        flash(f'Error generating syntax tree: {str(e)}', 'danger')
        return render_template('index.html')

@app.route('/save_results', methods=['POST'])
def save_results():
    english_text = request.form.get('english_text', '').strip()

    if not english_text:
        flash('No text to save.', 'warning')
        return render_template('index.html')

    try:
        translation_result = translator.translate_with_stats(english_text)
        grammatical_info = translator.get_grammatical_info(english_text)
        frequency_list = translator.get_frequency_list(english_text, grammatical_info)

        full_data = {
            **translation_result,
            'grammatical_info': grammatical_info,
            'frequency_list': frequency_list
        }

        filename = translator.save_to_file(full_data)
        flash(f'Results saved to {filename}', 'success')

        sentences = sent_tokenize(english_text)
        return render_template('index.html',
                               translation_result=translation_result,
                               grammatical_info=grammatical_info,
                               frequency_list=frequency_list,
                               sentences=sentences)

    except Exception as e:
        flash(f'Error saving results: {str(e)}', 'danger')
        return render_template('index.html')

@app.route('/print_results', methods=['POST'])
def print_results():
    english_text = request.form.get('english_text', '').strip()

    if not english_text:
        return "No text to print", 400

    try:
        translation_result = translator.translate_with_stats(english_text)
        grammatical_info = translator.get_grammatical_info(english_text)
        frequency_list = translator.get_frequency_list(english_text, grammatical_info)

        return render_template('print.html',
                               translation_result=translation_result,
                               grammatical_info=grammatical_info,
                               frequency_list=frequency_list)

    except Exception as e:
        return f"Error generating printable version: {str(e)}", 500

@app.route('/api/translate', methods=['POST'])
def api_translate():
    data = request.get_json()
    english_text = data.get('text', '').strip()

    if not english_text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        translation_result = translator.translate_with_stats(english_text)

        if translation_result.get('error'):
            return jsonify({'error': translation_result['translation']}), 500

        return jsonify({
            'translation': translation_result['translation'],
            'word_count': translation_result['word_count'],
            'translation_word_count': translation_result['translation_word_count'],
            'time_taken': translation_result['time_taken'],
            'cached': translation_result['cached']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)