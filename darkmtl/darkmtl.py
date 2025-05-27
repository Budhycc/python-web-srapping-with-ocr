import os
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import time

BASE_URL = "https://darkmtl.com/series/childhood-friend-of-the-zenith/"

def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " ._-" else "_" for c in name)

def get_series_info_and_chapters(series_url):
    res = requests.get(series_url)
    soup = BeautifulSoup(res.text, 'html.parser')

    series_title_tag = soup.select_one('div.series-titlex h2')
    if not series_title_tag:
        raise Exception("Tidak menemukan judul series di halaman utama")
    series_title = series_title_tag.text.strip()

    chapter_links = []
    chapter_div = soup.select_one('div.series-chapter')
    if not chapter_div:
        raise Exception("Tidak menemukan div.series-chapter")

    for li in chapter_div.select('ul.series-chapterlist > li'):
        info_div = li.select_one('div.flexch-infoz')
        if info_div:
            a_tags = info_div.select('a')
            if len(a_tags) >= 2:
                href = a_tags[1].get('href')
                if href:
                    if href.startswith('http'):
                        chapter_links.append(href)
                    else:
                        chapter_links.append("https://darkmtl.com" + href)

    chapter_links.reverse()  # urut dari awal ke akhir

    return series_title, chapter_links

def scrape_chapter(chapter_url):
    res = requests.get(chapter_url)
    soup = BeautifulSoup(res.text, 'html.parser')

    title_tag = soup.select_one('h1.entry-title') or soup.select_one('h2.entry-title') or soup.select_one('h2') or soup.select_one('title')
    if title_tag:
        chapter_title = title_tag.text.strip()
    else:
        chapter_title = chapter_url.rstrip('/').split('/')[-1].replace('-', ' ').title()

    content_div = soup.select_one('div.content')
    if not content_div:
        raise ValueError(f"Tidak menemukan <div class='content'> di {chapter_url}")

    content_text = content_div.get_text(separator='\n').strip()
    content_html = str(content_div)

    return chapter_title, content_html, content_text

def save_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def translate_long_text(text, target_lang='id', batch_size=4500):
    translator = GoogleTranslator(source='auto', target=target_lang)
    translated_parts = []
    start = 0
    length = len(text)

    while start < length:
        end = start + batch_size
        if end < length:
            # Usahakan potong di spasi terakhir supaya tidak memotong kata
            end = text.rfind(' ', start, end)
            if end == -1 or end <= start:
                end = start + batch_size

        chunk = text[start:end].strip()
        if chunk:
            translated_chunk = translator.translate(chunk)
            translated_parts.append(translated_chunk)
        start = end

    return "\n".join(translated_parts)

def main():
    series_title, chapters = get_series_info_and_chapters(BASE_URL)
    print(f"Judul series: {series_title}")
    print(f"Jumlah chapter: {len(chapters)}")

    base_path = os.path.join("download", sanitize_filename(series_title))
    original_dir = os.path.join(base_path, "original")
    translated_dir = os.path.join(base_path, "translated")
    os.makedirs(original_dir, exist_ok=True)
    os.makedirs(translated_dir, exist_ok=True)

    for idx, chapter_link in enumerate(chapters, 1):
        print(f"[{idx}/{len(chapters)}] Scraping {chapter_link}")
        try:
            chapter_title, html_content, text_content = scrape_chapter(chapter_link)

            safe_title = sanitize_filename(chapter_title)
            # Simpan file asli
            save_file(os.path.join(original_dir, f"{safe_title}.html"), html_content)
            save_file(os.path.join(original_dir, f"{safe_title}.txt"), text_content)

            # Translate teks panjang dengan batch, lalu simpan
            translated_text = translate_long_text(text_content)
            save_file(os.path.join(translated_dir, f"{safe_title}.txt"), translated_text)

            time.sleep(1.5)

        except Exception as e:
            print(f"❌ Gagal memproses {chapter_link}: {e}")

if __name__ == "__main__":
    main()
