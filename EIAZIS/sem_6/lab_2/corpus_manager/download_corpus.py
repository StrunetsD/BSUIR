import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
import os
import time

def download_wikisource_text(url, output_path):
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content = soup.find('div', {'class': 'mw-parser-output'})
        if not content:
            return False
        
        for unwanted in content.find_all(['table', 'div'], class_=['navbox', 'infobox', 'metadata']):
            unwanted.decompose()
        
        text = []
        for element in content.find_all(['p', 'h2', 'h3', 'div.mw-heading']):
            text.append(element.get_text())
        
        full_text = '\n\n'.join(text)
        
        full_text = re.sub(r'\[\d+\]', '', full_text)
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

def download_text(url, output_path):
    if 'wikisource.org' in url:
        return download_wikisource_text(url, output_path)
    else:
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            
            text = response.text
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False

def download_corpus_from_file(sources_file='sources.txt', output_folder='uploads'):
    Path(output_folder).mkdir(exist_ok=True)
    
    if not os.path.exists(sources_file):
        print(f"Файл {sources_file} не найден")
        return
    
    with open(sources_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    success_count = 0
    total_count = 0
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = [p.strip() for p in line.split('|')]
        if len(parts) != 5:
            print(f"Неверный формат строки: {line}")
            continue
        
        title, url, author, genre, fmt = parts
        filename = re.sub(r'[^\w\s-]', '', title)
        filename = re.sub(r'[-\s]+', '_', filename)
        filename = f"{filename}.{fmt}"
        output_path = Path(output_folder) / filename
        
        total_count += 1
        print(f"Загрузка: {title}")
        
        if download_text(url, output_path):
            success_count += 1
            print(f"  Сохранено: {filename}")
        else:
            print(f"  Не удалось загрузить: {url}")
        
        time.sleep(1)
    
    print(f"\nЗагружено {success_count} из {total_count} файлов")

if __name__ == "__main__":
    download_corpus_from_file()