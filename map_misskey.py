
import time
import random
import logging
import requests
from flickrapi import FlickrAPI
from PIL import Image, ExifTags, ImageOps
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelень)- %(message)s')

# Настройка Misskey
MISSKEY_API_BASE_URL = 'https://misskey.de'
ACCESS_TOKEN = ''

# Настройка Flickr API
FLICKR_PUBLIC = ''
FLICKR_SECRET = ''
flickr = FlickrAPI(FLICKR_PUBLIC, FLICKR_SECRET, format='parsed-json')

# Настройка OpenCage Geocoder API
OPENCAGE_API_KEY = ''

# Максимальные допустимые размеры изображений на Misskey
MAX_WIDTH = 4096
MAX_HEIGHT = 4096

HASHTAGS = ["#photo", "#foto", "#flickr", "#photography", "#map", "#world", "#peace"]

def correct_image_orientation(image):
    try:
        exif = image._getexif()
        if exif:
            for tag, value in exif.items():
                if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == 'Orientation':
                    if value == 3:
                        image = image.rotate(180, expand=True)
                    elif value == 6:
                        image = image.rotate(270, expand=True)
                    elif value == 8:
                        image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return image

def resize_image(image_path):
    with Image.open(image_path) as img:
        img = correct_image_orientation(img)
        original_size = img.size
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.ANTIALIAS)
        new_size = img.size
        img.save(image_path)
        return original_size, new_size

def extract_exif_data(image_path):
    with Image.open(image_path) as img:
        exif_data = {}
        exif = img._getexif()
        if exif:
            for tag, value in exif.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                if decoded in ["FNumber", "ExposureTime", "ISOSpeedRatings", "FocalLength", "Model"]:
                    exif_data[decoded] = value
        return exif_data

def format_exif_data(exif_data):
    exif_message = ""
    if "FNumber" in exif_data:
        exif_message += f"Диафрагма: f/{exif_data['FNumber']}\n"
    if "ExposureTime" in exif_data:
        exif_message += f"Выдержка: {exif_data['ExposureTime']} сек\n"
    if "ISOSpeedRatings" in exif_data:
        exif_message += f"ISO: {exif_data['ISOSpeedRatings']}\n"
    if "FocalLength" in exif_data:
        exif_message += f"Фокусное расстояние: {exif_data['FocalLength']} мм\n"
    if "Model" in exif_data:
        exif_message += f"Камера: {exif_data['Model']}\n"
    return exif_message

def post_to_misskey(message, image_paths):
    logging.info("Отправка поста в Misskey...")
    media_ids = []
    for image_path in image_paths:
        original_size, new_size = resize_image(image_path)
        logging.info(f"Изображение изменено с {original_size} до {new_size}")
        with open(image_path, 'rb') as f:
            files = {'file': f}
            headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
            response = requests.post(f'{MISSKEY_API_BASE_URL}/api/drive/files/create', files=files, headers=headers)
            response_data = response.json()
            media_ids.append(response_data['id'])
    
    payload = {
        'i': ACCESS_TOKEN,
        'text': message,
        'fileIds': media_ids
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f'{MISSKEY_API_BASE_URL}/api/notes/create', json=payload, headers=headers)
    logging.info("Пост успешно опубликован.")

def get_random_hashtags():
    return " ".join(random.sample(HASHTAGS, 6))

def search_and_post():
    while True:
        try:
            logging.info("Поиск фотографии на Flickr...")
            photo, title, author, lat, lon = search_for_photo()

            if photo:
                logging.info("Фотография найдена. Получение адреса...")
                address = get_address(lat, lon)
                if not address:
                    address = f"{lat}, {lon}"
                logging.info("Создание скриншота карты...")
                map_image_path = create_map_screenshot(lat, lon)
                hashtags = get_random_hashtags()
                message = f"📸 Автор фото: {author}"

                if title:
                    message += f"\n📌 Название: {title}"

                if address:
                    message += f"\n🏠 Адрес: {address}"

                exif_data = extract_exif_data('photo.jpg')
                if exif_data:
                    exif_message = format_exif_data(exif_data)
                    if exif_message:
                        message += f"\n\n⚙ EXIF данные:\n{exif_message}"

                message += f"\n🌐 Широта: {lat}\n🌐 Долгота: {lon}\n{hashtags}"
                post_to_misskey(message, ['photo.jpg', map_image_path])
                
                delay = random.randint(3600, 10800)  # Случайное время от 1 до 3 часов в секундах
                hours = delay // 3600
                minutes = (delay % 3600) // 60
                logging.info(f"Следующий пост будет опубликован через {hours} часов и {minutes} минут.")
                time.sleep(delay)
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            time.sleep(60)  # Ожидание 1 минуту перед повторной попыткой в случае ошибки

def search_for_photo():
    photos = flickr.photos.search(has_geo=1, per_page=10, extras='geo')
    photo = random.choice(photos['photos']['photo'])
    photo_id = photo['id']
    lat = photo['latitude']
    lon = photo['longitude']

    info = flickr.photos.getInfo(photo_id=photo_id)
    author = info['photo']['owner']['username']
    title = info['photo']['title']['_content']

    sizes = flickr.photos.getSizes(photo_id=photo_id)
    image_url = sizes['sizes']['size'][-1]['source']

    image_data = requests.get(image_url).content
    with open('photo.jpg', 'wb') as file:
        file.write(image_data)

    return photo, title, author, lat, lon

def get_address(lat, lon):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={OPENCAGE_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data['results']:
        address_components = data['results'][0]['components']
        address_parts = [
            address_components.get('road'),
            address_components.get('suburb'),
            address_components.get('city'),
            address_components.get('state'),
            address_components.get('postcode'),
            address_components.get('country')
        ]
        # Формируем адрес только из непустых компонентов
        address = ', '.join(part for part in address_parts if part)
        return address
    else:
        return None

def create_map_screenshot(lat, lon):
    # URL карты
    map_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=15/{lat}/{lon}"

    # Настройка Selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1024,768')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-software-rasterizer')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.get(map_url)
    time.sleep(5)  # Ждем, пока карта загрузится полностью

    # Скрытие ненужных элементов с помощью JavaScript
    driver.execute_script("""
        document.querySelectorAll('header, .sidebar, .search-container, .sidebar-content-container').forEach(el => el.style.display = 'none');
    """)
    time.sleep(2)  # Ждем, пока элементы скрываются

    # Найти элемент карты и сделать скриншот этой области
    map_element = driver.find_element(By.ID, 'map')  # Пожалуйста, проверьте правильный ID элемента карты на странице
    location = map_element.location
    size = map_element.size

    screenshot = driver.get_screenshot_as_png()
    driver.quit()

    # Обрезать изображение до размера элемента карты
    map_image = Image.open(BytesIO(screenshot))
    left = location['x'] + 411
    top = location['y']
    right = location['x'] + size['width']
    bottom = location['y'] + size['height']
    map_image = map_image.crop((left, top, right, bottom))

    map_image_path = 'map.png'
    map_image.save(map_image_path)

    return map_image_path

if __name__ == "__main__":
    search_and_post()
