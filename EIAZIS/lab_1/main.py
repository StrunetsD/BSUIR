import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import os
import re
import pymorphy3
import json

morph = pymorphy3.MorphAnalyzer()

class WordEntry:
    def __init__(self, word, role, form, sentence_num):
        self.word = word
        self.role = role
        self.form = form
        self.sentence_num = sentence_num

    def to_dict(self):
        return {
            'word': self.word,
            'role': self.role,
            'form': self.form,
            'sentence_num': self.sentence_num
        }

    @staticmethod
    def from_dict(data):
        return WordEntry(data['word'], data['role'], data['form'], data['sentence_num'])

    def __str__(self):
        return f"{self.word} ({self.form}) - {self.role} в предложении {self.sentence_num}"

class TextAnalyzer:
    def __init__(self):
        self.entries = []

    def analyze(self, text):
        sentences = re.split(r'[.!?]\s*', text)
        for i, sentence in enumerate(sentences):
            words = re.findall(r'\b\w+\b', sentence)
            for word in words:
                parsed = morph.parse(word)[0]
                role = self.detect_role(parsed)
                form = ', '.join(filter(None, [parsed.tag.case, parsed.tag.tense, parsed.tag.number,
                                               parsed.tag.gender])) or 'неопределено'
                entry = WordEntry(parsed.normal_form, role, form, i + 1)
                self.entries.append(entry)
        self.entries.sort(key=lambda x: x.word)

    def detect_role(self, parsed):
        if 'NOUN' in parsed.tag:
            if 'nomn' in parsed.tag:
                return 'подлежащее'
            elif 'gent' in parsed.tag:
                return 'дополнение'
        elif 'ADJF' in parsed.tag:
            return 'определение'
        elif 'VERB' in parsed.tag:
            return 'сказуемое'
        return 'неопределено'

    def save_to_file(self, filepath):
        existing_entries = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_entries = [WordEntry.from_dict(d) for d in json.load(f)]
            except Exception:
                pass

        all_entries = existing_entries + self.entries
        seen = set()
        unique_entries = []
        for e in all_entries:
            key = (e.word, e.role, e.form, e.sentence_num)
            if key not in seen:
                seen.add(key)
                unique_entries.append(e)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([e.to_dict() for e in unique_entries], f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            self.entries = [WordEntry.from_dict(d) for d in json.load(f)]

    def filter_entries(self, keyword):
        return [e for e in self.entries if keyword.lower() in e.word.lower() or keyword.lower() in e.role.lower() or keyword.lower() in e.form.lower()]

    def delete_entry(self, index):
        if 0 <= index < len(self.entries):
            del self.entries[index]

    def update_entry(self, index, new_entry):
        if 0 <= index < len(self.entries):
            self.entries[index] = new_entry

class App:
    def __init__(self, root):
        self.analyzer = TextAnalyzer()
        self.root = root
        self.root.title("Анализатор русского текста")

        self.text = tk.Text(root, height=10, width=80)
        self.text.pack()

        self.button_frame = tk.Frame(root)
        self.button_frame.pack()

        self.load_button = tk.Button(self.button_frame, text="Загрузить файл", command=self.load_file)
        self.load_button.grid(row=0, column=0)

        self.analyze_button = tk.Button(self.button_frame, text="Анализировать", command=self.analyze_text)
        self.analyze_button.grid(row=0, column=1)

        self.save_button = tk.Button(self.button_frame, text="Сохранить словарь", command=self.save_dict)
        self.save_button.grid(row=0, column=2)

        self.load_dict_button = tk.Button(self.button_frame, text="Загрузить словарь", command=self.load_dict)
        self.load_dict_button.grid(row=0, column=3)

        self.filter_button = tk.Button(self.button_frame, text="Фильтр / Поиск", command=self.filter_entries)
        self.filter_button.grid(row=0, column=4)

        self.edit_button = tk.Button(self.button_frame, text="Редактировать", command=self.edit_entry)
        self.edit_button.grid(row=0, column=5)

        self.delete_button = tk.Button(self.button_frame, text="Удалить", command=self.delete_entry)
        self.delete_button.grid(row=0, column=6)

        self.help_button = tk.Button(self.button_frame, text="Помощь", command=self.show_help)
        self.help_button.grid(row=0, column=7)

        self.tree = ttk.Treeview(root, columns=("Слово", "Форма", "Роль", "Предложение"), show='headings')
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
        self.tree.pack()

    def show_help(self):
        help_text = (
            "Возможности программы:\n"
            "- Загрузка текстовых файлов (.txt, .rtf)\n"
            "- Морфологический анализ текста (определение ролей слов)\n"
            "- Отображение результатов в виде таблицы\n"
            "- Сохранение результатов в файл JSON (словарь)\n"
            "- Загрузка сохранённого словаря\n"
            "- Фильтрация и поиск по словам, ролям и формам\n"
            "- Редактирование записей в словаре\n"
            "- Удаление записей\n"
        )
        messagebox.showinfo("Помощь", help_text)

    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("Rich Text Format", "*.rtf")])
        if not filepath:
            return
        if filepath.endswith(".txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        elif filepath.endswith(".rtf"):
            try:
                import striprtf
                with open(filepath, "r", encoding="utf-8") as f:
                    content = striprtf.rtf_to_text(f.read())
            except ImportError:
                messagebox.showerror("Ошибка", "Для обработки RTF требуется установить библиотеку striprtf")
                return
        else:
            messagebox.showerror("Ошибка", "Неподдерживаемый формат файла")
            return
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, content)

    def analyze_text(self):
        content = self.text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Пустой текст", "Введите или загрузите текст для анализа.")
            return
        self.analyzer.analyze(content)
        self.update_tree(self.analyzer.entries)

    def update_tree(self, entries):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for idx, entry in enumerate(entries):
            self.tree.insert("", tk.END, iid=str(idx), values=(entry.word, entry.form, entry.role, entry.sentence_num))

    def save_dict(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filepath:
            self.analyzer.save_to_file(filepath)
            messagebox.showinfo("Сохранено", "Словарь сохранён успешно.")

    def load_dict(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath:
            self.analyzer.load_from_file(filepath)
            self.update_tree(self.analyzer.entries)
            messagebox.showinfo("Загружено", "Словарь загружен успешно.")

    def filter_entries(self):
        keyword = simpledialog.askstring("Поиск", "Введите ключевое слово для фильтрации:")
        if keyword:
            filtered = self.analyzer.filter_entries(keyword)
            self.update_tree(filtered)

    def delete_entry(self):
        selected = self.tree.selection()
        if selected:
            index = int(selected[0])
            self.analyzer.delete_entry(index)
            self.update_tree(self.analyzer.entries)

    def edit_entry(self):
        selected = self.tree.selection()
        if selected:
            index = int(selected[0])
            entry = self.analyzer.entries[index]

            new_word = simpledialog.askstring("Редактирование", "Слово:", initialvalue=entry.word)
            new_form = simpledialog.askstring("Редактирование", "Форма:", initialvalue=entry.form)
            new_role = simpledialog.askstring("Редактирование", "Роль:", initialvalue=entry.role)
            new_sentence = simpledialog.askinteger("Редактирование", "Номер предложения:", initialvalue=entry.sentence_num)

            if new_word and new_form and new_role and new_sentence:
                new_entry = WordEntry(new_word, new_role, new_form, new_sentence)
                self.analyzer.update_entry(index, new_entry)
                self.update_tree(self.analyzer.entries)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
