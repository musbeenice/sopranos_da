from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

import time  # Для пауз между действиями

import pandas as pd  # Для работы с данными в pd.DataFrame

from bs4 import BeautifulSoup  # Для парсинга HTML

# Настройки Chrome для стабильной работы
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # Открываем браузер на полный экран
options.add_experimental_option("detach", True)  # Браузер не закроется автоматически после скрипта

# Инициализация драйвера Chrome с автоматической установкой нужной версии
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# URL страницы с cast и production crew сериала "The Sopranos" с сайта IMDb
url = "https://www.imdb.com/title/tt0141842/fullcredits/"

driver.get(url)  # Открываем страницу в браузере

# Список для хранения данных о режиссерах
directors = []

# Ожидаем появления якоря на секцию с режиссерами (ждем до 20 секунд)
directors_anchor = WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.XPATH, "//a[@href='#director']"))
)

# Находим всю секцию с режиссерами, используя найденный якорь
directors_section = directors_anchor.find_element(By.XPATH, "./ancestor::section[1]")

# Находим всех режиссеров в секции (элементы списка)
directors_list = directors_section.find_elements(By.XPATH, ".//li[contains(@class, 'ipc-metadata-list-summary-item')]")

# Обрабатываем каждого режиссера
for director in directors_list:

    # Ищем кнопку "episodes" для режиссера
    element = director.find_elements(By.XPATH, ".//button[contains(@class, 'ipc-link') and contains(., 'episode')]")

    # Кликаем на кнопку через ActionChains для надежности
    ActionChains(driver).move_to_element(element[0]).click().perform()

    # Ожидаем появления попапа с информацией
    popup = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.ipc-popover__content, div[role='dialog']"))
    )

    # Пытаемся найти вкладки с сезонами (если это сериал с несколькими сезонами)
    try:
        season_tabs = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.ipc-tab[role='tab']"))
        )

        for tab in season_tabs:
            try:
                # Прокручиваем к вкладке и кликаем
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
                ActionChains(driver).move_to_element(tab).click().perform()
                time.sleep(1)  # Пауза для загрузки данных

                # Парсим HTML попапа с BeautifulSoup
                popup_html = popup.get_attribute('outerHTML')
                soup = BeautifulSoup(popup_html, 'lxml')

                # Извлекаем имя режиссера
                dir_name = soup.find('h3', class_='ipc-title__text').text.strip()

                # Находим все эпизоды, снятые данным режиссером
                episodes_containers = soup.find_all('a',
                                                    class_='ipc-list__item sc-19e3c1d-2 dhRnuM episodic-credits-bottomsheet__menu-item')

                # Сохраняем данные по каждому эпизоду
                for season in episodes_containers:
                    line = season.find_all('li', class_='ipc-inline-list__item')
                    season_ep = [s.text.strip() for s in line][0]  # Получаем номер сезона и эпизода
                    directors.append({'director': dir_name,
                                      'season_ep': season_ep})
            except Exception as e:
                print(f"Ошибка при обработке сезона {tab.text.strip()}: {str(e)}")
                continue
    except:
        # Обработка случая, когда у режиссера только один эпизод (нет вкладок сезонов)
        popup_html = popup.get_attribute('outerHTML')
        soup = BeautifulSoup(popup_html, 'lxml')

        dir_name = soup.find('h3', class_='ipc-title__text').text.strip()
        episode_container = soup.find('a',
                                      class_='ipc-list__item sc-19e3c1d-2 dhRnuM episodic-credits-bottomsheet__menu-item')
        line = episode_container.find_all('li', class_='ipc-inline-list__item')
        season_ep = line[0].text.strip()
        directors.append({'director': dir_name,
                          'season_ep': season_ep})

    # Закрываем попап нажатием клавиши ESC
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(0.5)  # Небольшая пауза для закрытия попапа

# Создаем DataFrame с собранными данными
sopranos_directors = pd.DataFrame(directors)

# Закрываем браузер
driver.quit()

# Сохраняем данные в CSV (раскомментировать при необходимости)
# sopranos_directors.to_csv('sopranos_directors.csv', index=False)
