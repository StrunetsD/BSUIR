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

    def exact_search_entries(self, keyword):
        return [e for e in self.entries if e.word.lower() == keyword.lower()]

    def delete_entry(self, index):
        if 0 <= index < len(self.entries):
            del self.entries[index]

    def update_entry(self, index, new_entry):
        if 0 <= index < len(self.entries):
            self.entries[index] = new_entry
            
    def get_grouped_entries(self):
        """Группирует записи по слову. Возвращает словарь: {'слово': [список записей]}"""
        groups = {}
        for entry in self.entries:
            if entry.word not in groups:
                groups[entry.word] = []
            groups[entry.word].append(entry)
        return groups

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

        self.filter_button = tk.Button(self.button_frame, text="Фильтрация", command=self.filter_entries)
        self.filter_button.grid(row=0, column=4)

        self.exact_search_button = tk.Button(self.button_frame, text="Точный поиск", command=self.exact_search_entries)
        self.exact_search_button.grid(row=0, column=5)

        self.edit_button = tk.Button(self.button_frame, text="Редактировать", command=self.edit_entry)
        self.edit_button.grid(row=0, column=6)

        self.delete_button = tk.Button(self.button_frame, text="Удалить", command=self.delete_entry)
        self.delete_button.grid(row=0, column=7)

        self.help_button = tk.Button(self.button_frame, text="Помощь", command=self.show_help)
        self.help_button.grid(row=0, column=8)

        self.tree = ttk.Treeview(root, columns=("Слово", "Форма", "Роль", "Предложение"), show='headings')
        self.tree.heading("Слово", text="Слово")
        self.tree.heading("Форма", text="Форма")
        self.tree.heading("Роль", text="Роль")
        self.tree.heading("Предложение", text="Предложение №")
        
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
        self.tree.pack()

    def show_help(self):
        help_text = (
            "Возможности программы:\n"
            "- Загрузка текстовых файлов (.txt, .rtf)\n"
            "- Морфологический анализ текста\n"
            "- Двойной клик по слову показывает все контексты использования\n"
            "- Фильтрация и Точный поиск\n"
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
        self.update_tree()

    def update_tree(self, entries_to_show=None):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        if entries_to_show:
            for idx, entry in enumerate(entries_to_show):
                self.tree.insert("", tk.END, iid=str(idx), values=(entry.word, entry.form, entry.role, entry.sentence_num))
        else:
            groups = self.analyzer.get_grouped_entries()
            for word, occurrences in groups.items():
                first = occurrences[0]
                count = len(occurrences)
                
                sent_info = str(first.sentence_num)
                if count > 1:
                    sent_info += f" ({count-1})"
                
                self.tree.insert("", tk.END, iid=word, values=(first.word, first.form, first.role, sent_info))

    def on_tree_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        
        groups = self.analyzer.get_grouped_entries()
        
        if item_id in groups:
            occurrences = groups[item_id]
            self.open_details_window(item_id, occurrences)
        else:
            word_val = self.tree.item(selection[0])['values'][0]
            matches = [e for e in self.analyzer.entries if e.word == word_val]
            if matches:
                self.open_details_window(word_val, matches)

    def open_details_window(self, word, occurrences):
        top = tk.Toplevel(self.root)
        top.title(f"Контексты слова: '{word}'")
        top.geometry("500x300")

        label = tk.Label(top, text=f"Слово '{word}' встречается {len(occurrences)} раз(а):", font=("Arial", 12, "bold"))
        label.pack(pady=10)

        detail_tree = ttk.Treeview(top, columns=("Форма", "Роль", "Предложение"), show='headings')
        detail_tree.heading("Форма", text="Грамматическая форма")
        detail_tree.heading("Роль", text="Роль в предложении")
        detail_tree.heading("Предложение", text="№ Предложения")
        
        detail_tree.column("Форма", width=200)
        detail_tree.column("Роль", width=150)
        detail_tree.column("Предложение", width=100)

        for entry in occurrences:
            detail_tree.insert("", tk.END, values=(entry.form, entry.role, entry.sentence_num))

        detail_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        btn_close = tk.Button(top, text="Закрыть", command=top.destroy)
        btn_close.pack(pady=5)

    def save_dict(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filepath:
            self.analyzer.save_to_file(filepath)
            messagebox.showinfo("Сохранено", "Словарь сохранён успешно.")

    def load_dict(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath:
            self.analyzer.load_from_file(filepath)
            self.update_tree() 
            messagebox.showinfo("Загружено", "Словарь загружен успешно.")

    def filter_entries(self):
        keyword = simpledialog.askstring("Поиск", "Введите ключевое слово для фильтрации (частичное совпадение):")
        if keyword:
            filtered = self.analyzer.filter_entries(keyword)
            self.update_tree(filtered)

    def exact_search_entries(self):
        keyword = simpledialog.askstring("Точный поиск", "Введите слово для полного совпадения:")
        if keyword:
            found = self.analyzer.exact_search_entries(keyword)
            if not found:
                messagebox.showinfo("Результат", "Слово не найдено.")
            self.update_tree(found)

    def delete_entry(self):
        selected = self.tree.selection()
        if selected:
            item_values = self.tree.item(selected[0])['values']
            word_to_delete = item_values[0]
            
            for i, entry in enumerate(self.analyzer.entries):
                if entry.word == word_to_delete:
                    self.analyzer.delete_entry(i)
                    break
            
            self.update_tree()

    def edit_entry(self):
        selected = self.tree.selection()
        if selected:
            item_values = self.tree.item(selected[0])['values']
            word_to_edit = item_values[0]
            
            target_entry = None
            idx = -1
            for i, entry in enumerate(self.analyzer.entries):
                if entry.word == word_to_edit:
                    target_entry = entry
                    idx = i
                    break
            
            if target_entry:
                new_word = simpledialog.askstring("Редактирование", "Слово:", initialvalue=target_entry.word)
                new_form = simpledialog.askstring("Редактирование", "Форма:", initialvalue=target_entry.form)
                new_role = simpledialog.askstring("Редактирование", "Роль:", initialvalue=target_entry.role)
                new_sentence = simpledialog.askinteger("Редактирование", "Номер предложения:", initialvalue=target_entry.sentence_num)

                if new_word and new_form and new_role and new_sentence:
                    new_entry = WordEntry(new_word, new_role, new_form, new_sentence)
                    self.analyzer.update_entry(idx, new_entry)
                    self.update_tree()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()