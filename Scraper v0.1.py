
import random
import asyncio
import aiohttp
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import pandas as pd

async def fetch_page(session, url):
    headers = {'User-Agent': user_agents()}  # Wybieramy losowy User-Agent
    async with session.get(url, headers=headers) as response:
        return await response.text()

def user_agents():
    user_agents_list = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299'
    ]
    return random.choice(user_agents_list)


def display_offers(url):
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")  # Uruchamia przeglądarkę w trybie bezokienkowym

    # Wskazujemy odpowiedni sterownik
    driver = webdriver.Firefox(options=options)

    try:
        # Pobieramy stronę przy pomocy Selenium
        driver.get(url)

        # Oczekujemy na pojawienie się komunikatu o cookies i klikamy w przycisk akceptacji
        wait = WebDriverWait(driver, 5)
        accept_button = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler')))
        accept_button.click()

        time.sleep(3)  # Czekamy na załadowanie strony (możesz dostosować czas, jeśli potrzeba)

        offers_list = []

        while True:
            # Przewijamy stronę do samego dołu, aby załadować wszystkie oferty
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Dodajemy opóźnienie, aby dać czas na załadowanie wszystkich ofert

            # Pobieramy źródło strony i przekazujemy je do BeautifulSoup
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            offers_elements = soup.select('[data-cy="listing-item-title"]')
            offers_links = soup.select('[data-cy="listing-item-link"]')

            for index, offer_element in enumerate(offers_elements, start=1):
                print(f"Oferta {index}:")
                print(offer_element.prettify())  # Wyświetl całą zawartość oferty
                # Pobierz link oferty
                if index <= len(offers_links):  # Sprawdź, czy indeks mieści się w zakresie listy linków
                    offer_link = "www.otodom.pl" + offers_links[index - 1].get('href')
                    print(f"Link do oferty {index}: {offer_link}")
                    print("=" * 50)

                    offer_info = {
                        'index': index,
                        'offer_element': offer_element,
                        'offer_link': offer_link,
                    }
                    offers_list.append(offer_info)

            # Sprawdzamy, czy przycisk "Następna strona" jest widoczny
            next_page_button = driver.find_element(By.CSS_SELECTOR, '[data-cy="pagination.next-page"]')
            if not next_page_button.is_displayed():
                print("Nie znaleziono kolejnej strony lub wystąpił błąd.")
                break

            next_page_button.click()
            time.sleep(3)  # Dodajemy opóźnienie, aby dać czas na załadowanie nowej zawartości

            # Sprawdzamy, czy zawartość strony się zmieniła po przejściu do kolejnej strony
            if page_source == driver.page_source:
                print("Nie znaleziono kolejnej strony lub wystąpił błąd.")
                break

    except Exception as e:
        print(f"Nie udało się pobrać strony: {e}")
    finally:
        driver.quit()  # Kończymy działanie przeglądarki

    return offers_list


async def get_offer_data(url, index):

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get("https://" + url)
    time.sleep(5)  # Czekamy na załadowanie strony

    # Przewijamy stronę w dół wielokrotnie, aż do momentu, gdy wszystkie dane zostaną załadowane
    max_attempts = 10
    attempts = 0
    while attempts < max_attempts:
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        time.sleep(2)  # Czekamy na załadowanie kolejnych danych
        attempts += 1

        # Sprawdzamy, czy wszystkie interesujące nas elementy są już załadowane
        if are_elements_loaded(driver):
            break

    html_content = driver.page_source

    driver.quit()  # Zamykamy przeglądarkę

    soup = BeautifulSoup(html_content, 'html.parser')

    data_dict = {
        'Nr oferty w Otodom': [],
        'Tytuł ogłoszenia': [],
        'Cena': [],
        'Cena za m²': [],
        'Adres': [],
        'Powierzchnia': [],
        'Liczba Pokoi': [],
        'Piętro': [],
        'Czynsz': [],
        'Forma własności': [],
        'Stan wykończenia': [],
        'Balkon / ogród / taras': [],
        'Ogrzewanie': [],
        'Rynek': [],
        'Typ ogloszeniodawcy': [],
        'Rok budowy': [],
        'Rodzaj zabudowy': [],
        'material': [],
        'Okna': [],
        'Winda': [],
        'Media': [],
        'Zabezpieczenia': [],
        'Informacje dodatkowe': [],
        'Opis': [],
        'Potral': 'otodom.pl',
        'Link': url
    }

    try:
        offer_number = soup.select_one('.css-i4bwcc.e1ualqfi3').text
        data_dict['Nr oferty w Otodom'].append(offer_number)

    except AttributeError:
        data_dict['Nr oferty w Otodom'] = None

    try:
        ad_title = soup.select_one('[data-cy="adPageAdTitle"]').text
        data_dict['Tytuł ogłoszenia'].append(ad_title)

    except AttributeError:
        data_dict['Tytuł ogłoszenia'] = None

    try:
        price = soup.select_one('[aria-label="Cena"]').text
        data_dict['Cena'].append(price)
    except AttributeError:
        data_dict['Cena'] = None

    try:
        price_per_square_meter = soup.select_one('[aria-label="Cena za metr kwadratowy"]').text
        data_dict['Cena za m²'].append(price_per_square_meter)

    except AttributeError:
        data_dict['Cena za m²'] = None

    try:
        address = soup.select_one('a[aria-label="Adres"]').text
        data_dict['Adres'].append(address)

    except AttributeError:
        data_dict['Adres'] = None

    try:
        area = soup.select_one('.css-1wi2w6s').text
        data_dict['Powierzchnia'].append(area)

    except AttributeError:
        data_dict['Powierzchnia'] = None

    try:
        rooms = soup.select_one('[aria-label="Liczba pokoi"]').text
        data_dict['Liczba Pokoi'].append(rooms)

    except AttributeError:
        data_dict['Liczba Pokoi'] = None

    try:
        floor = soup.select_one('[aria-label="Piętro"]').text
        data_dict['Piętro'].append(floor)

    except AttributeError:
        data_dict['Piętro'] = None

    try:
        rent = soup.select_one('[aria-label="Czynsz"]').text
        data_dict['Czynsz'].append(rent)

    except AttributeError:
        data_dict['Czynsz'] = None

    try:
        ownership = soup.select_one('[aria-label="Forma własności"]').text
        data_dict['Forma własności'].append(ownership)

    except AttributeError:
        data_dict['Forma własności'] = None

    try:
        condition = soup.select_one('[aria-label="Stan wykończenia"]').text
        data_dict['Stan wykończenia'].append(condition)

    except AttributeError:
        data_dict['Stan wykończenia'] = None

    try:
        garden = soup.select_one('[aria-label="Balkon / ogród / taras"]').text
        data_dict['Balkon / ogród / taras'].append(garden)

    except AttributeError:
        data_dict['Balkon / ogród / taras'] = None

    try:
        heating = soup.select_one('[aria-label="Ogrzewanie"]').text
        data_dict['Ogrzewanie'].append(heating)

    except AttributeError:
        data_dict['Ogrzewanie'] = None

    try:
        market = soup.select_one('[aria-label="Rynek"]').text
        data_dict['Rynek'].append(market)

    except AttributeError:
        data_dict['Rynek'] = None

    try:
        owner = soup.select_one('[aria-label="Typ ogłoszeniodawcy"]').text
        data_dict['Typ ogloszeniodawcy'].append(owner)

    except AttributeError:
        data_dict['Typ ogloszeniodawcy'] = None

    try:
        year = soup.select_one('[aria-label="Rok budowy"]').text
        data_dict['Rok budowy'].append(year)

    except AttributeError:
        data_dict['Rok budowy'] = None

    try:
        build_type = soup.select_one('[aria-label="Rodzaj zabudowy"]').text
        data_dict['Rodzaj zabudowy'].append(build_type)

    except AttributeError:
        data_dict['Rodzaj zabudowy'] = None

    try:
        material = soup.select_one('[aria-label="Materiał budynku"]').text
        data_dict['material'].append(material)

    except AttributeError:
        data_dict['material'] = None

    try:
        window = soup.select_one('[aria-label="Okna"]').text
        data_dict['Okna'].append(window)

    except AttributeError:
        data_dict['Okna'] = None

    try:
        elevator = soup.select_one('[aria-label="Winda"]').text
        data_dict['Winda'].append(elevator)

    except AttributeError:
        data_dict['Winda'] = None

    try:
        media = soup.select_one('[aria-label="Media"]').text
        data_dict['Media'].append(media)

    except AttributeError:
        data_dict['Media'] = None

    try:
        secure = soup.select_one('[aria-label="Zabezpieczenia"]').text
        data_dict['Zabezpieczenia'].append(secure)

    except AttributeError:
        data_dict['Zabezpieczenia'] = None

    try:
        additional_info = soup.select_one('[aria-label="Informacje dodatkowe"]').text
        data_dict['Informacje dodatkowe'].append(additional_info)

    except AttributeError:
        data_dict['Informacje dodatkowe'] = None

    try:
        description = soup.select_one('[data-cy="adPageAdDescription"]').text
        data_dict['Opis'].append(description)

    except AttributeError:
        data_dict['Opis'] = None

    # Tworzymy DataFrame z danymi
    df = pd.DataFrame(data_dict, index=[index])

    # Edycja danych w df - usuwamy zbędne fragmenty tekstowe
    df['Nr oferty w Otodom'] = df['Nr oferty w Otodom'].str.replace("Nr oferty w Otodom: ", "")
    df['Powierzchnia'] = df['Powierzchnia'].str.replace('m²', '')
    df['Liczba Pokoi'] = df['Liczba Pokoi'].str.replace('Liczba pokoi', '')
    df['Piętro'] = df['Piętro'].str.replace('Piętro', '')
    df['Czynsz'] = df['Czynsz'].str.replace('Czynsz', '')
    df['Forma własności'] = df['Forma własności'].str.replace('Forma własności', '')
    df['Stan wykończenia'] = df['Stan wykończenia'].str.replace('Stan wykończenia', '')
    df['Balkon / ogród / taras'] = df['Balkon / ogród / taras'].str.replace('Balkon / ogród / taras', '')
    df['Ogrzewanie'] = df['Ogrzewanie'].str.replace('Ogrzewanie', '')
    df['Rynek'] = df['Rynek'].str.replace('Rynek', '')
    df['Rok budowy'] = df['Rok budowy'].str.replace('Rok budowy', '')
    df['Rodzaj zabudowy'] = df['Rodzaj zabudowy'].str.replace('Rodzaj zabudowy', '')
    df['material'] = df['material'].str.replace('Materiał budynku', '')
    df['Okna'] = df['Okna'].str.replace('Okna', '')
    df['Winda'] = df['Winda'].str.replace('Winda', '')
    df['Media'] = df['Media'].str.replace('Media', '')
    df['Zabezpieczenia'] = df['Zabezpieczenia'].str.replace('Zabezpieczenia', '')
    df['Informacje dodatkowe'] = df['Informacje dodatkowe'].str.replace('Informacje dodatkowe', '')
    df['Cena'] = df['Cena'].str.replace('zł', '').str.replace(' ', '').str.replace(',', '.')
    df['Cena za m²'] = df['Cena za m²'].str.replace('zł/m²', '').str.replace(' ', '').str.replace(',', '.')

    # Zwracamy DataFrame z danymi
    return df


def are_elements_loaded(driver):
    # Funkcja sprawdzająca, czy wszystkie interesujące nas elementy na stronie są już załadowane
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Powierzchnia"]')))
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Liczba pokoi"]')))
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Piętro"]')))
        # Dodaj tutaj pozostałe elementy, które Cię interesują
        return True
    except:
        return False

def process_all_links(links_list):
    data_list = []

    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, link_info in enumerate(links_list, start=1):
            offer_link = link_info['offer_link']
            task = asyncio.create_task(get_offer_data(session, offer_link, index))
            tasks.append(task)

        # Oczekiwanie na zakończenie wszystkich zadań asynchronicznych
        completed_tasks, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

        for task in completed_tasks:
            df = task.result()
            if df is not None and not df.empty:
                data_list.append(df)

    if not data_list:
        print("Nie udało się pobrać żadnych ofert.")
        return None

    resulting_dataframe = pd.concat(data_list, ignore_index=False)
    output_filename = "Biurko/scrapper/wyniki_ofert-test-async.xlsx"
    resulting_dataframe.to_excel(output_filename, index=True)

    return resulting_dataframe


# Przykładowe użycie funkcji display_offers
url = 'https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/zachodniopomorskie/szczecin/szczecin/szczecin?distanceRadius=15&page=1&limit=36&ownerTypeSingleSelect=ALL&areaMax=60&by=DEFAULT&direction=DESC&viewType=listing'

# Wywołanie funkcji display_offers
offers_links_list = display_offers(url)

# Wywołanie funkcji process_all_links
resulting_dataframe = process_all_links(offers_links_list)

