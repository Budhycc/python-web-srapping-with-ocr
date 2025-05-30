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

# Set path Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Setup WebDriver
options = webdriver.EdgeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=2560,4000")

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
        while start < len(text):
            chunk = text[start:start+max_chunk]
            translated_parts.append(translator.translate(chunk))
            start += max_chunk
        return "\n".join(translated_parts)
    except Exception as e:
        return f"⚠️ ERROR_TRANSLATE: {e}"

def log_failure(path, episode_title, episode_url, error_message):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(f"{episode_title} | {episode_url} | {error_message}\n")

try:
    series_url = input("Masukan Link Series-nya (contoh: https://requiemtls.com/series/{title}): ")
    driver.get(series_url)
    wait = WebDriverWait(driver, 15)

    try:
        series_title_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.entry-title")))
        series_title = sanitize_filename(series_title_el.text)
    except:
        series_title = "Unknown_Series"

    base_folder = os.path.join("download", series_title)
    base_folder_translated = os.path.join(base_folder, "translated")
    log_path = os.path.join(base_folder, "failed.log")
    os.makedirs(base_folder, exist_ok=True)
    os.makedirs(base_folder_translated, exist_ok=True)

    try:
        accept_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cmplz-buttons .cmplz-btn.cmplz-accept")))
        accept_btn.click()
        time.sleep(2)
    except:
        pass

    episode_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".eplister ul li a")))
    episode_urls = [link.get_attribute("href") for link in episode_links][::-1]

    print("\n📚 Daftar Episode:")
    for i, url in enumerate(episode_urls, 1):
        print(f"{i}. {url.split('/')[-2]}")

    choice = input("\nKetik 'all' untuk download semua, atau masukkan nomor episode (misal: 1,3,5): ")

    if choice.strip().lower() != "all":
        try:
            selected_indexes = [int(i.strip()) for i in choice.split(',') if i.strip().isdigit()]
            episode_urls = [episode_urls[i - 1] for i in selected_indexes if 0 < i <= len(episode_urls)]
        except Exception as e:
            print(f"❌ Input tidak valid: {e}")
            driver.quit()
            exit()

    for idx, episode_url in enumerate(episode_urls, 1):
        print(f"\n▶️ Memproses Episode {idx}: {episode_url}")
        driver.get(episode_url)
        time.sleep(3)

        driver.execute_script("document.body.style.zoom='150%'")
        time.sleep(1)

        try:
            episode_title_el = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.entry-title"))
            )
            episode_title = sanitize_filename(episode_title_el.text)
        except:
            episode_title = f"Episode_{idx}"

        try:
            content = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.epcontent.entry-content"))
            )
        except:
            error_msg = "Konten tidak ditemukan"
            print(f"❌ Episode {idx} gagal: {error_msg}")
            log_failure(log_path, episode_title, episode_url, error_msg)
            continue

        driver.execute_script("arguments[0].scrollIntoView();", content)
        time.sleep(1)

        total_width = int(content.size['width'] * 1.5)
        total_height = int(content.size['height'] * 1.5)
        driver.set_window_size(total_width + 100, total_height + 300)
        time.sleep(1)

        screenshot_path = os.path.join(base_folder, f"{episode_title}.png")
        driver.save_screenshot(screenshot_path)

        print(f"🔠 Menjalankan OCR Episode {idx}...")
        try:
            img = Image.open(screenshot_path)
            text = pytesseract.image_to_string(img, lang='eng')

            text_path = os.path.join(base_folder, f"{episode_title}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"✅ OCR disimpan: {text_path}")
        except Exception as e:
            error_msg = f"OCR gagal: {e}"
            print(f"❌ {error_msg}")
            log_failure(log_path, episode_title, episode_url, error_msg)
            continue

        print(f"🌐 Menerjemahkan Episode {idx} ke Bahasa Indonesia...")
        translated_text = translate_text(text)
        if translated_text and not translated_text.startswith("⚠️ ERROR_TRANSLATE"):
            translated_path = os.path.join(base_folder_translated, f"{episode_title}.translated.txt")
            with open(translated_path, 'w', encoding='utf-8') as f:
                f.write(translated_text)
            print(f"✅ Terjemahan disimpan: {translated_path}")
        else:
            error_msg = "Terjemahan gagal atau kosong"
            print(f"⚠️ {error_msg}")
            log_failure(log_path, episode_title, episode_url, error_msg)

finally:
    driver.quit()
    print("\n✅ Semua proses selesai. Log kegagalan (jika ada) tersimpan di 'failed.log'")
