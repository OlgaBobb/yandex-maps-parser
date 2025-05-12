import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import streamlit as st
import os
import tempfile
from webdriver_manager.chrome import ChromeDriverManager

# Настройка страницы Streamlit
st.set_page_config(page_title="Парсер Яндекс.Карт", page_icon="🗺️")
st.title("Парсер Яндекс.Карт")
st.markdown("Загрузите Excel-файл со списком ссылок на Яндекс.Карты (в первом столбце, без заголовка).")

# Настройки браузера
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Функция парсинга
def parse_yandex_maps(url, driver):
    """Парсинг данных с Яндекс.Карт"""
    driver.get(url)
    time.sleep(random.uniform(2, 4))
    
    def get_text(xpath, default="Не найден"):
        try:
            element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            return element.text if element.text else default
        except:
            return default
    
    def get_phone(xpath, default="Не найден"):
        try:
            element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            phone = element.text
            if phone:  # Проверяем, что phone не None и не пустой
                return phone.split("\n")[0]
            return default
        except:
            return default
    
    try:
        rating_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'business-rating-badge-view__rating-text')]"))
        )
        rating = rating_element.text if rating_element.text else "Не найдено"
    except:
        rating = "Не найдено"
    
    try:
        reviews_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'business-header-rating-view__text')]"))
        )
        reviews = reviews_element.get_attribute("aria-label").strip() if reviews_element.get_attribute("aria-label") else "Не найдено"
    except:
        reviews = "Не найдено"
    
    data = {
        "Ссылка": url,
        "Название": get_text("//h1"),
        "Адрес": get_text("//div[contains(@class, 'business-contacts-view__address')]/a"),
        "Метро": get_text("//div[contains(@class, 'masstransit-stops-view__stop-name')]"),
        "Часы работы": get_text("//div[contains(@class, 'business-card-working-status-view__text')]"),
        "Телефон": get_phone("//div[contains(@class, 'card-phones-view__phone-number')]"),
        "Сайт": get_text("//span[contains(@class, 'business-urls-view__text')]"),
        "Средняя оценка": rating,
        "Количество оценок": reviews
    }
    return data

# Функция обработки файла
def process_file(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, header=None)
        urls = df[0].dropna().tolist()
        if not urls:
            return None, "Ошибка: Файл не содержит ссылок."
        driver = setup_driver()
        results = [parse_yandex_maps(url, driver) for url in urls]
        driver.quit()
        df_result = pd.DataFrame(results)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            output_path = tmp.name
            df_result.to_excel(output_path, index=False)
        return output_path, "✅ Данные сохранены в yandex_maps_data.xlsx"
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return None, f"Ошибка: {str(e)}"

# Streamlit-интерфейс
uploaded_file = st.file_uploader("Выберите Excel-файл", type=["xlsx"])
if uploaded_file is not None:
    if st.button("Запустить парсинг"):
        with st.spinner("Выполняется парсинг..."):
            output_path, status = process_file(uploaded_file)
            st.write(status)
            if output_path:
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="Скачать результат",
                        data=f,
                        file_name="yandex_maps_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                os.unlink(output_path)