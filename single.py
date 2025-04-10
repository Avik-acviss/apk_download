import time
import csv
import random
import concurrent.futures
import requests
import tempfile

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

############################################
# Helper function to create Selenium driver
############################################
def get_driver():
    print("[DEBUG] Initializing Chrome driver...")
    chrome_driver_path = r"C:\Users\Acviss-ml\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"  # Update this path if needed
    service = Service(chrome_driver_path)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--incognito")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    # --- FRESH PROFILE EACH RUN ---
    temp_profile = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_profile}")

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36"
    ]
    chosen_agent = random.choice(user_agents)
    print(f"[DEBUG] Using user agent: {chosen_agent}")
    options.add_argument(f"user-agent={chosen_agent}")

    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.maximize_window()
    print("[DEBUG] Chrome driver launched successfully.")
    return driver

############################################
# Scrolling function with prints
############################################
def scroll_page(driver, iterations=3, pause=2):
    try:
        print("[DEBUG] Starting scroll_page function...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(iterations):
            print(f"[DEBUG] Scroll iteration {i+1}")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("[DEBUG] No more scrolling available.")
                break
            last_height = new_height
        print("[DEBUG] Finished scrolling.")
    except Exception as e:
        print(f"[DEBUG] Scrolling error: {e}")

############################################
# Yandex CAPTCHA bypass helper
############################################
def yandex_robot(driver):
    print("[DEBUG] Attempting Yandex CAPTCHA bypass...")
    try:
        captcha_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//input[@id="js-button"]')))
        print("[DEBUG] CAPTCHA button found, clicking...")
        captcha_button.click()
        print("[DEBUG] CAPTCHA clicked successfully.")
    except Exception as e:
        print("[WARNING] Manual CAPTCHA verification required. Please solve the CAPTCHA.")

############################################
# CAPTCHA detection helper
############################################
def check_for_captcha(driver):
    try:
        if driver.find_element(By.XPATH, '//iframe[contains(@title, "reCAPTCHA")]'):
            print("[DEBUG] Google reCAPTCHA detected.")
            return True
        if driver.find_elements(By.XPATH, '//input[@id="js-button"]') or driver.find_elements(By.XPATH, '//button[contains(text(), "I am human")]'):
            print("[DEBUG] Yandex bot verification detected.")
            return True
    except Exception as e:
        pass
    return False

############################################
# Generic URL scraping function
############################################
def scrape_urls(driver, search_url, engine_name, no_of_pages, xpath, next_button_xpath):
    print(f"[INFO] Starting scrape on {engine_name} for URL: {search_url}")
    urls = []
    if engine_name == "Yandex":
        yandex_robot(driver)
    driver.get(search_url)
    if check_for_captcha(driver):
        print(f"[WARNING] CAPTCHA detected for {engine_name}. Please solve it manually.")
    current_page = 0
    while current_page < no_of_pages:
        current_page += 1
        print(f"[INFO] Scraping page {current_page} of {engine_name}...")
        if engine_name == "Yandex":
            yandex_robot(driver)
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except Exception as e:
            print(f"[ERROR] Error waiting for elements on page {current_page} of {engine_name}: {e}")
            break
        links = driver.find_elements(By.XPATH, xpath)
        print(f"[DEBUG] Found {len(links)} links on page {current_page}.")
        for link in links:
            url = link.get_attribute('href')
            if url:
                urls.append((url, engine_name))
        if current_page < no_of_pages:
            try:
                next_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, next_button_xpath))
                )
                print("[DEBUG] Clicking next page button...")
                driver.execute_script("arguments[0].click();", next_button)
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"[ERROR] Error clicking next button for {engine_name}: {e}")
                print("[DEBUG] No next button found or reached last page.")
                break
    driver.quit()
    print(f"[INFO] Completed scraping for {engine_name}.")
    return urls

############################################
# Search engine scrapper functions
############################################
def url_scrapper_google(product_name, no_of_pages):
    print("[INFO] Starting Google scraper...")
    driver = get_driver()
    search_url = f"https://www.google.com/search?q={product_name}&num=10"
    return scrape_urls(driver, search_url, "Google", no_of_pages,
                       "//div[@class='yuRUbf']//a", "//span[contains(text(), 'Next')]")

def url_scrapper_bing(product_name, no_of_pages):
    print("[INFO] Starting Bing scraper...")
    driver = get_driver()
    search_url = f"https://www.bing.com/search?q={product_name}"
    return scrape_urls(driver, search_url, "Bing", no_of_pages,
                       "//li[@class='b_algo']//h2/a", "//a[@class='sb_pagN sb_pagN_bp b_widePag sb_bp ']")

def url_scrapper_yahoo(product_name, no_of_pages):
    print("[INFO] Starting Yahoo scraper...")
    driver = get_driver()
    search_url = f"https://in.search.yahoo.com/search?p={product_name}"
    return scrape_urls(driver, search_url, "Yahoo", no_of_pages,
                       "//h3/a", "//a[@class='next' and contains(text(), 'Next')]")

def url_scrapper_yandex(product_name, no_of_pages):
    print("[INFO] Starting Yandex scraper...")
    driver = get_driver()
    search_url = f"https://yandex.com/search/?text={product_name}"
    driver.get(search_url)
    if check_for_captcha(driver):
        try:
            captcha_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//input[@id="js-button"]')))
            print("[DEBUG] CAPTCHA button found on Yandex, clicking...")
            driver.execute_script("arguments[0].click();", captcha_button)
            captcha_button.click()
        except Exception as e:
            print("[WARNING] Manual CAPTCHA verification required on Yandex.")
            input("Press Enter after solving the CAPTCHA...")
    return scrape_urls(driver, search_url, "Yandex", no_of_pages,
                       "//a[contains(@class,'organic__url')]",
                       "//div[@class='Pager-ListItem Pager-ListItem_type_next']//a[@class='VanillaReact Pager-Item Pager-Item_type_next' and contains(text(), 'next')]")

def url_scrapper_duckduckgo(product_name, no_of_pages):
    print("[INFO] Starting DuckDuckGo scraper...")
    driver = get_driver()
    search_url = f"https://duckduckgo.com/?q={product_name}&ia=web"
    return scrape_urls(driver, search_url, "DuckDuckGo", no_of_pages,
                       "//div[@class='pAgARfGNTRe_uaK72TAD']//a",
                       "//div[@class='rdxznaZygY2CryNa5yzk']//button[@id='more-results' and contains(text(), 'More results')]")

############################################
# Save results to CSV
############################################
def save_to_csv(data, filename="search_results.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["URL", "Search Engine"])
        writer.writerows(data)
    print(f"[INFO] Search results CSV saved successfully as {filename}")

############################################
# Main collection function to aggregate URLs
############################################
def main_collect():
    product_name = input("Enter the product name to search: ")
    google_pages = int(input("Enter the number of pages to search for Google: "))
    bing_pages = int(input("Enter the number of pages to search for Bing: "))
    yahoo_pages = int(input("Enter the number of pages to search for Yahoo: "))
    yandex_pages = int(input("Enter the number of pages to search for Yandex: "))
    duckduckgo_pages = int(input("Enter the number of pages to search for DuckDuckGo: "))
    all_results = []
    all_results.extend(url_scrapper_google(product_name, google_pages))
    all_results.extend(url_scrapper_bing(product_name, bing_pages))
    all_results.extend(url_scrapper_yahoo(product_name, yahoo_pages))
    all_results.extend(url_scrapper_yandex(product_name, yandex_pages))
    all_results.extend(url_scrapper_duckduckgo(product_name, duckduckgo_pages))
    save_to_csv(all_results)
    print("[INFO] URL collection complete.")

############################################
# Second-stage normal driver for details scrape
############################################
def get_normal_driver():
    print("[DEBUG] Initializing normal Chrome driver for details scrape...")
    chrome_driver_path = r"C:\Users\Acviss-ml\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"  # Update this path if needed
    service = Service(chrome_driver_path)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--incognito")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    # --- FRESH PROFILE EACH RUN ---
    temp_profile = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_profile}")

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36"
    ]
    chosen_agent = random.choice(user_agents)
    print(f"[DEBUG] Using user agent for details scrape: {chosen_agent}")
    options.add_argument(f"user-agent={chosen_agent}")
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.maximize_window()
    print("[DEBUG] Normal Chrome driver launched successfully for details scraping.")
    return driver

############################################
# Get HTTP response code with timeout
############################################
def get_response_code(url):
    try:
        print(f"[DEBUG] Checking HTTP response for URL: {url}")
        response = requests.get(url, timeout=10)
        return response.status_code
    except requests.exceptions.RequestException:
        print(f"[WARNING] Request failed for URL: {url}")
        return None

############################################
# Details scraper, checking for download buttons
############################################
def handle_popups(driver):
    try:
        close_button_xpaths = [
            "//button[contains(text(), 'Close')]",
            "//button[contains(text(), 'close')]",
            "//button[contains(text(), 'No thanks')]",
            "//button[contains(text(), 'Dismiss')]",
            "//div[contains(@class, 'modal')]//button[contains(text(), '×')]",
            "//button[@class='close']",
            "//button[contains(@class,'close')]"
        ]
        for xpath in close_button_xpaths:
            elements = driver.find_elements(By.XPATH, xpath)
            for element in elements:
                if element.is_displayed():
                    element.click()
                    time.sleep(1)
                    print("[DEBUG] Pop-up closed.")
    except Exception as e:
        print(f"[DEBUG] Exception in popup handling: {e}")

def check_for_download_button(driver):
    download_button_xpaths = [
        "//div[contains(@class, 'button-group') and contains(@class, 'download')]//a[contains(@class, 'button') and contains(@title, 'download') and contains(., 'Get the latest version')]",
        "//a[contains(@class, 'downloadAPK') and contains(@title, 'Download APK')]",
        "//a[contains(@class, 'jump-downloading-btn') and contains(., 'Download APK')]",
        "//a[contains(@class, 'page__btn-dl') and contains(text(), 'Скачать')]",
        "//a[contains(@class, 'button last') and contains(@title, 'download facebook free')]",
        "(//div[contains(@class, 'gradient-button__AppStoreDownload-sc-1troloh-3') and contains(text(), 'Download')])[2]",
        "//a[contains(@class, 'download_button') and contains(@title, 'Facebook for Android Download')]",
        "//a[contains(@class, 'da download_apk') and contains(@title, 'Download Facebook latest version apk')]",
        "//div[contains(@class, 'download-module__col')]//a[contains(@class, 'button-download-direct') and contains(., 'Скачать бесплатно APK')]",
        "//div[contains(@class, 'cjj0l') and contains(text(), 'Click to download file')]",
        "//*[contains(text(),'Get')]",
        "//*[contains(text(),'Install')]",
        "//*[contains(text(),'Download')]",
        "//div[contains(text(),'Download')]",
        "//*[contains(text(),'Free Download')]",
        "//button[contains(@id, 'detail-download-button')]",
        "//a[contains(@id, 'button-download')]",
        "//button[@id= 'detail-download-button']",
        "(//div[@class='s-button-app__main']/strong)[1]",
        "//a[contains(@class, 'download') and contains(@class, 'wp-block-button__link')]",
        "(//a[@rel='nofollow' and contains(@class, 'download_link') and contains(@class, 'btn') and contains(@href, 'cloudfront.net')][.//span[contains(text(), 'Start Download')]])[2]",
        "//a[contains(@href, 'modfyp.com/download') and contains(@class, 'btnDownload') and contains(@class, 'btnGotoDownloadMain')]",
        "//a[contains(@class, 'downloadButton') and contains(@class, 'variantsButton') and contains(@href, '#downloads')]",
        "(//a[@rel='nofollow' and contains(@class, 'download_link') and contains(@class, 'btn') and contains(@href, 'cloudfront.net')])[2]",
        "//a[contains(@class, 'dwn1') and contains(@href, 'download')]",
        "(//a[contains(@class, 'download_link') and contains(@href, 'cloudfront.net')])[2]",
        "//a[contains(@class, 'download-button') and contains(@href, 'get-facebook.html')]",
        "(//a[contains(@class, 'game-versions__downloads-button') and contains(., 'Скачать apk')])[1]",
        "//a[contains(@href, '/download') and contains(text(), 'Download Latest APK')]",
        "(//a[contains(@class, 'btn_download') and contains(@href, 'download=links')])[1]",
        "//a[contains(@class, 'btn_apkdownload') and contains(@href, 'download=1')]",
        "//a[contains(@class, 'downloadAPK') and contains(@href, 'download=links')]",
        "//a[contains(@class, 'button last') and contains(@href, 'uptodown.com/android/download')]",
        "//button[contains(@class, '_42ft') and contains(., 'Download APK')]",
        "//a[contains(@href, '/download') and contains(text(), 'Download Latest APK')]",
        "(//a[contains(@class, 'game-versions__downloads-button') and contains(@href, '/dwn/')])[1]",
        "(//a[contains(@class, 'accent_color') and contains(@href, 'android-apk-download')])[1]",
        "//a[contains(@class, 'page__btn-dl') and contains(text(), 'Скачать')]",
        "//a[contains(@href, '/goto') and contains(text(), 'Как скачать?')]",
        "(//a[contains(@class, 'button') and contains(@href, '/facebook/com.facebook.katana/download/apk')])[2]",
        "//a[contains(@class, 'buttonDownload') and contains(@href, 'com-facebook-katana/download')]",
        "(//a[contains(@class, 'dllink') and contains(@href, 'download.it/android/download')])[1]",
        "(//a[contains(@class, 'accent_color') and contains(@href, 'android-apk-download')])[1]",
        "(//div[@class='table-cell rowheight addseparator expand pad dowrap-break-all']/a[@class='accent_color' and contains(@href, '/apk/facebook-2/facebook/variant-')])[1]",
        "(//div[@class='table-cell rowheight addseparator expand pad dowrap-break-all']/a[@class='accent_color']/@href)[1]",
        "(//div[@class='table-cell rowheight addseparator expand pad dowrap-break-all']/span[contains(@class, 'apkm-badge')][1]/text())[1]",
        "(//div[contains(@class,'table-cell')]/a[@class='accent_color']/@href)[1]",
        "//a[@class='button last']/@href",
        "//a[contains(@class, 'box_alov')]/@href",
        "//a[contains(text(), 'Download APK File from APK4Fun')]/@href",
        "//a[@class='download-link' and contains(text(), 'Скачать')]/@href",
        "//a[@class='full-news-d' and contains(text(), 'СКАЧАТЬ')]/@href",
        "//div[@class='name']/text()[1]",
        "//div[contains(@class, 'to-dl') and contains(@class, 'button')]",
        "//a[@href='https://androidlomka.com/downloads/123867/' and @class='button download' and text()='Скачать последнюю версию']",
        "//a[@href='https://apktake.com/apps/facebook/download' and @class='btn btn-lg btn-outline-light w-75' and text()='Скачать']",
        "//a[@href='https://r-static-assets.androidapks.com/rdata/f75e7ee31abb959a483952171c0e0b28/com.facebook.katana_v476.0.0.49.74-454214857_Android-8.0.apk' and contains(@class, 'wp-block-button__link') and strong[text()='Скачать']]",
        "//a[@href='/get-24837-facebook.html' and contains(@class, 'btn-download') and contains(normalize-space(), 'СКАЧАТЬ')]",
        "//a[@class='btn btn-dl' and @href='/download/com.facebook.katana/fa370b1827feccd7f882fb19ee36d688/' and @title='download Facebook APK now']",
        "//a[@href='https://file.apkdone.io/s/8f6XqcFn4om7WGJ/download' and @title='Download Facebook 436.0.0.0.28' and contains(@class, 'version-download-btn')]",
        "//a[@href='https://apkpure.tools/ru/facebook/com.facebook.katana/download' and contains(., 'Скачать APK')]",
        "//a[@href='https://apkpure.ph/ru/facebook/com.facebook.katana/download' and contains(., 'Скачать APK')]",
        "//img[@src='https://androidapksfree.com/wp-content/uploads/2014/11/Facebook-APK-1-85x85.png' and @alt='Facebook 507.0.0.66.49 APK']",
        "(//h5[@class='appRowTitle wrapText marginZero block-on-mobile']/a[@class='fontBlack'])[1]",
        "(//a[@class='accent_color' and contains(@href, 'facebook-434-0-0-36-115')])[1]",
        "//a[@class='button last' and contains(@href, 'facebook.fr.uptodown.com/android/telecharger')]",
        "(//a[@class='fontBlack' and contains(@href, '/apk/facebook-2/facebook/facebook-293-0-0-43-120-release')])[1]",
        "//div[@class='download-button__DownloadContainer-sc-18tslsf-0 iupaOQ']//div[@class='gradient-button__AppStoreDownload-sc-1troloh-3 cCqocC track-download-button' and text()='Descargar']",
        "(//h5[@class='appRowTitle wrapText marginZero block-on-mobile']/a[@class='fontBlack' and contains(text(), 'Facebook 451.0.0.45.109')])[1]",
        "//a[@class='button last' and @href='https://facebook.uptodown.com/android/descargar']",
        "(//div[@class='table-cell rowheight addseparator expand pad dowrap-break-all']//a[@class='accent_color' and contains(@href, 'facebook-435-0-0-42-112')])[1]",
        "(//div[@class='table-cell rowheight addseparator expand pad dowrap-break-all']//a[@class='accent_color' and contains(@href, 'facebook-301-0-0-0-54')])[1]",
        "(//a[@class='fontBlack' and contains(@href, 'facebook-508-0-0-50-47')])[1]",
        "(//a[@class='accent_color' and contains(@href, 'facebook-434-0-0-36-115')])[1]",
        "(//a[@class='accent_color' and contains(@href, 'facebook-457-0-0-54-84')])[1]",
        "(//a[@class='accent_color' and contains(@href, 'facebook-494-0-0-55-73')])[1]",
        "//a[@class='download' and contains(@href, 'facebook.com/download/direct')]",
        "//a[@class='dwn1' and contains(@href, 'apk.watch/download')]",
        "//a[@class='dit-dlbtn dllink mb-3 w-100 text-left align-left btn btn-lg btn-block  download_link' and contains(@href, 'cloudfront.net')]",
        "//img[@alt='Facebook 507.0.0.66.49 APK']"

    ]
    for xpath in download_button_xpaths:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            if elements and any(elem.is_displayed() for elem in elements):
                return True
        except Exception as e:
            pass
    return False

def check_download_on_url(url, engine_name):
    print(f"[INFO] Checking download button on: {url}")
    driver = get_driver()
    try:
        driver.get(url)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except TimeoutException:
            print("[WARNING] Page took too long to load")

        # Allow time for the page to load
        handle_popups(driver)

        # Check for download button on the main page
        if check_for_download_button(driver):
            print(f"[DEBUG] Download button found on main page for {url}")
            return True

        # Check for download button inside iframes, if present
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            print(f"[DEBUG] {len(iframes)} iframe(s) detected on {url}")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    if check_for_download_button(driver):
                        print(f"[DEBUG] Download button found in an iframe for {url}")
                        driver.switch_to.default_content()
                        return True
                    driver.switch_to.default_content()
                except Exception as e:
                    print(f"[DEBUG] Exception while checking iframe: {e}")
                    driver.switch_to.default_content()
        return False

    except WebDriverException as e:
        if "ERR_CONNECTION_TIMED_OUT" in str(e):
            print(f"[TIMEOUT] Skipping timed-out URL: {url}")
        else:
            print(f"[ERROR] WebDriverException at {url}: {e}")
        return False

    except Exception as e:
        print(f"[ERROR] Unexpected error on {url}: {e}")
        return False

    finally:
        try:
            driver.quit()
        except:
            pass

from concurrent.futures import ThreadPoolExecutor, as_completed

def process_all_urls_concurrently(url_rows, max_workers=6):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_row = {executor.submit(check_download_on_url, row["URL"], row["Search Engine"]): row for row in url_rows}
        for future in as_completed(future_to_row):
            row = future_to_row[future]
            try:
                has_download = future.result()
                if has_download:
                    results.append({
                        "URL": row["URL"],
                        "Download Button": "Yes",
                        "Search Engine": row["Search Engine"]
                    })
            except Exception as exc:
                print(f"[ERROR] {row['URL']} generated an exception: {exc}")
                # Don't save if there's an error or no button
    return results


def process_csv_downloads_concurrent(input_csv="search_results.csv", output_csv="download_results.csv"):
    url_rows = []
    with open(input_csv, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            url_rows.append(row)

    # Process URL checks concurrently
    results = process_all_urls_concurrently(url_rows, max_workers=6)

    if results:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ["URL", "Download Button", "Search Engine"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for res in results:
                writer.writerow(res)
        print(f"[INFO] CSV saved with {len(results)} URLs that have download buttons.")
    else:
        print("[INFO] No download buttons found — CSV not created.")

############################################
# Main execution: Run both sections sequentially
############################################
if __name__ == "__main__":
    main_collect()
    process_csv_downloads_concurrent()