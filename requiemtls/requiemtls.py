from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from PIL import Image
import time
import os
import pytesseract
from deep_translator import GoogleTranslator
import traceback

# Set path Tesseract di PC kamu
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Setup Edge webdriver dengan opsi headless
options = webdriver.EdgeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=2560,4000")
options.add_argument("--log-level=3")  # Error only

driver = webdriver.Edge(
    service=EdgeService(EdgeChromiumDriverManager().install()),
    options=options
)

def sanitize_filename(text):
    return "".join(c for c in text if c.isalnum() or c in "._- ").strip()

def translate_text(text, dest_lang="id", max_chunk=4000):
    try:
        translator = GoogleTranslator(source='auto', target=dest_lang)
        translated_parts = []
        start = 0
        length = len(text)
        while start < length:
            chunk = text[start:start+max_chunk]
            # print(f"🧠 Menerjemahkan chunk teks mulai dari karakter {start} sampai {start+len(chunk)}")
            translated_chunk = translator.translate(chunk)
            translated_parts.append(translated_chunk)
            start += max_chunk
        return "\n".join(translated_parts)
    except Exception as e:
        print(f"⚠️ Gagal translate: {e}")
        traceback.print_exc()
        return None

try:
    series_url = input("Masukan Link Series-nya (contoh: https://requiemtls.com/series/{title}): ")
    print(f"🌐 Mengakses URL series: {series_url}")
    driver.get(series_url)
    wait = WebDriverWait(driver, 15)

    # Ambil judul series
    try:
        series_title_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.entry-title")))
        series_title = sanitize_filename(series_title_el.text)
        print(f"📚 Judul series ditemukan: {series_title}")
    except Exception as e:
        print(f"⚠️ Gagal mengambil judul series: {e}")
        traceback.print_exc()
        series_title = "Unknown_Series"

    # Buat folder
    base_folder = os.path.join("download", series_title)
    base_folder_translated = os.path.join(base_folder, "translated")
    os.makedirs(base_folder, exist_ok=True)
    os.makedirs(base_folder_translated, exist_ok=True)
    print(f"📁 Folder base dibuat: {base_folder}")
    print(f"📁 Folder terjemahan dibuat: {base_folder_translated}")

    # Accept cookies jika ada
    try:
        accept_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cmplz-buttons .cmplz-btn.cmplz-accept")))
        accept_btn.click()
        print("✅ Cookie accepted.")
        time.sleep(2)
    except Exception:
        print("ℹ️ No cookie banner found atau sudah diterima sebelumnya.")

    # Ambil semua link episode
    episode_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".eplister ul li a")))
    episode_urls = [link.get_attribute("href") for link in episode_links][::-1]

    print("\nDaftar Episode:")
    for i, url in enumerate(episode_urls, 1):
        print(f"{i}. {url.split('/')[-2]}")

    choice = input(
        "\nKetik 'all' untuk download semua, atau masukkan nomor episode (contoh: 1,3,5 atau 4+ atau 2-6): "
    ).strip().lower()

    if choice == "all":
        pass  # Proses semua episode
    elif '+' in choice:
        try:
            start_index = int(choice.replace('+', '').strip()) - 1
            episode_urls = episode_urls[start_index:]
            print(f"🔢 Memproses episode mulai dari nomor {start_index+1} sampai akhir.")
        except Exception as e:
            print(f"❌ Input tidak valid: {e}")
            traceback.print_exc()
            driver.quit()
            exit()
    elif '-' in choice:
        try:
            start, end = [int(i.strip()) for i in choice.split('-')]
            episode_urls = episode_urls[start-1:end]
            print(f"🔢 Memproses episode dari nomor {start} sampai {end}.")
        except Exception as e:
            print(f"❌ Input tidak valid: {e}")
            traceback.print_exc()
            driver.quit()
            exit()
    else:
        try:
            selected_indexes = [int(i.strip()) for i in choice.split(',') if i.strip().isdigit()]
            episode_urls = [episode_urls[i - 1] for i in selected_indexes if 0 < i <= len(episode_urls)]
            print(f"🔢 Memproses episode nomor: {selected_indexes}")
        except Exception as e:
            print(f"❌ Input tidak valid: {e}")
            traceback.print_exc()
            driver.quit()
            exit()

    print(f"\n🔍 Akan memproses {len(episode_urls)} episode.")

    for idx, episode_url in enumerate(episode_urls, 1):
        print(f"\n▶️ Memproses Episode {idx}: {episode_url}")
        driver.get(episode_url)
        time.sleep(3)

        # Zoom in supaya screenshot jelas
        driver.execute_script("document.body.style.zoom='150%'")
        time.sleep(1)

        try:
            episode_title_el = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.entry-title"))
            )
            episode_title = sanitize_filename(episode_title_el.text)
            print(f"📝 Judul episode: {episode_title}")
        except Exception:
            episode_title = f"Episode_{idx}"
            print(f"⚠️ Gagal mengambil judul episode, pakai default: {episode_title}")

        try:
            content = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.epcontent.entry-content"))
            )
            print(f"✅ Konten episode ditemukan.")
        except Exception as e:
            print(f"❌ Episode {idx} gagal: konten tidak ditemukan.")
            traceback.print_exc()
            continue

        # Scroll konten supaya tampil sempurna
        driver.execute_script("arguments[0].scrollIntoView();", content)
        time.sleep(1)

        total_width = int(content.size['width'] * 1.5)
        total_height = int(content.size['height'] * 1.5)
        print(f"📐 Ukuran konten (width x height): {content.size['width']} x {content.size['height']}")
        print(f"📐 Ukuran window diset ke: {total_width + 100} x {total_height + 300}")

        driver.set_window_size(total_width + 100, total_height + 300)
        time.sleep(1)

        screenshot_path = os.path.join(base_folder, f"{episode_title}.png")
        driver.save_screenshot(screenshot_path)
        print(f"🖼️ Screenshot disimpan: {screenshot_path}")

        print(f"🔎 Menjalankan OCR pada Episode {idx}...")
        try:
            img = Image.open(screenshot_path)
            text = pytesseract.image_to_string(img, lang='eng')
            # print(f"📝 Hasil OCR (500 karakter pertama):\n{text[:500]}")

            text_path = os.path.join(base_folder, f"{episode_title}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"✅ OCR disimpan: {text_path}")

            print(f"🌐 Menerjemahkan Episode {idx} ke Bahasa Indonesia...")
            translated_text = translate_text(text, dest_lang="id")

            if translated_text:
                translated_path = os.path.join(base_folder_translated, f"{episode_title}.translated.txt")
                with open(translated_path, 'w', encoding='utf-8') as f:
                    f.write(translated_text)
                print(f"✅ Terjemahan disimpan: {translated_path}")
            else:
                print("⚠️ Terjemahan gagal atau hasil kosong.")

        except Exception as e:
            print(f"⚠️ Gagal OCR atau terjemahan Episode {idx}: {e}")
            traceback.print_exc()

finally:
    driver.quit()
    print("✅ Semua proses selesai.")
