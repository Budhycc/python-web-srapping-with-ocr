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

# Ganti path di bawah sesuai lokasi Tesseract di PC kamu
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Setup browser Edge
options = webdriver.EdgeOptions()
options.add_argument("--headless=new")  # Headless Chromium baru
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,3000")

driver = webdriver.Edge(
    service=EdgeService(EdgeChromiumDriverManager().install()),
    options=options
)

try:
    series_url = "https://requiemtls.com/series/how-to-survive-as-a-painter-in-a-dark-fantasy/"
    driver.get(series_url)
    wait = WebDriverWait(driver, 15)

    # Accept cookie jika muncul
    cookie_accepted = False
    try:
        accept_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".cmplz-buttons .cmplz-btn.cmplz-accept")))
        accept_btn.click()
        print("✅ Cookie accepted.")
        cookie_accepted = True
        time.sleep(2)
    except:
        print("ℹ️  No cookie banner found.")

    # Tunggu dan ambil semua episode link dari <ul> dalam .eplister
    episode_links = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".eplister ul li a"))
    )
    episode_urls = [link.get_attribute("href") for link in episode_links][::-1]  # dari episode pertama
    print(f"🔎 Menemukan {len(episode_urls)} episode.")

    # Buat folder penyimpanan
    os.makedirs("screenshots", exist_ok=True)

    # Loop semua episode
    for idx, episode_url in enumerate(episode_urls, 1):
        print(f"▶️ Memproses Episode {idx}: {episode_url}")
        driver.get(episode_url)
        time.sleep(3)

        # Temukan elemen konten
        try:
            content = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.epcontent.entry-content"))
            )
        except:
            print(f"❌ Episode {idx} gagal: tag konten tidak ditemukan.")
            continue

        # Scroll ke konten
        driver.execute_script("arguments[0].scrollIntoView();", content)
        time.sleep(1)

        # Ambil ukuran dan posisi elemen
        total_width = int(content.size['width'])
        total_height = int(content.size['height'])
        # x, y = int(content.location['x']), int(content.location['y'])

        # Ubah ukuran jendela agar cukup tinggi
        driver.set_window_size(total_width + 100, total_height + 300)
        time.sleep(1)

        # Screenshot layar penuh
        full_path = f"screenshots/episode{idx}.png"
        driver.save_screenshot(full_path)

        # OCR: Scan teks dari screenshot
        print(f"🔠 Menjalankan OCR untuk Episode {idx}...")
        try:
            img = Image.open(full_path)
            text = pytesseract.image_to_string(img, lang='eng')  # Ganti ke 'ind' jika teks bahasa Indonesia dan Tesseract punya modelnya

            text_output_file = f"screenshots/episode{idx}.txt"
            with open(text_output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"✅ Teks Episode {idx} disimpan: {text_output_file}")
        except Exception as e:
            print(f"⚠️ Gagal OCR Episode {idx}: {e}")


finally:
    driver.quit()
    print("✅ Semua proses selesai.")
