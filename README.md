# Python Web Scraping with OCR

Proyek ini bertujuan untuk melakukan web scraping pada novel daring yang kontennya di enkripsi dalam format gambar. Dengan memanfaatkan teknik Optical Character Recognition (OCR), proyek ini mengonversi teks dalam gambar menjadi teks digital yang dapat diproses lebih lanjut

## Fitur

* Scraping konten web novel yang di enkripsi.
* Menggunakan OCR untuk mengekstrak teks dari gambar.
* Menyimpan hasil ekstraksi dalam format teks dan kemudian di terjemahkan dengan deep-translator

## Prasyarat

Pastikan Anda telah menginstal dependensi berikut sebelum menjalankan proyek ini:

* Python 3.x
* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
* Pustaka Python:

  * `pytesseract`
  * `requests`
  * `BeautifulSoup4`
  * `Deep-translator`
  * `Pillow`

## Instalasi

1. **Clone repositori:**

   ```bash
   git clone https://github.com/Budhycc/python-web-srapping-with-ocr.git
   cd python-web-srapping-with-ocr
   ```



2. **Instal dependensi Python:**

   ```bash
   pip install -r requirements.txt
   ```



3. **Instal Tesseract OCR:**

   * **Windows:** Unduh dan instal dari [sini](https://github.com/tesseract-ocr/tesseract/wiki)


## Penggunaan

1. **Jalankan skrip utama:**

   ```bash
   python main.py
   ```



2. **Ikuti petunjuk yang diberikan untuk memasukkan URL halaman web novel yang ingin Anda scrape.**

3. **Hasil ekstraksi akan disimpan dalam file teks di direktori output.**
 
4. **Hasil ekstraksi txt akan di terjemahkan otomatis
