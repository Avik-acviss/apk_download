import time
import csv
import random
import undetected_chromedriver as uc
import atexit
import concurrent.futures
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options, use_subprocess=True)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.maximize_window()
    atexit.register(driver.quit)
    return driver


def scroll_page(driver, iterations=3, pause=2):
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(iterations):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    except Exception as e:
        print(f"[DEBUG] Scrolling error: {e}")


def yandex_robot(driver):
    print("Yandex bot verification detected. Attempting to bypass...")
    try:
        captcha_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//input[@id="js-button"]')))
        print("Button found, clicking...")
        captcha_button.click()
        print("CAPTCHA clicked successfully.")
    except Exception as e:
        print("Manual verification required. Please solve the CAPTCHA.")


def check_for_captcha(driver):
    try:
        if driver.find_element(By.XPATH, '//iframe[contains(@title, "reCAPTCHA")]'):
            print("Google reCAPTCHA detected.")
            return True
        if driver.find_elements(By.XPATH, '//input[@id="js-button"]') or driver.find_elements(By.XPATH,'//button[contains(text(), "I am human")]'):
            print("Yandex bot verification detected.")
            return True
    except:
        return False


def scrape_urls(driver, search_url, engine_name, no_of_pages, xpath, next_button_xpath):
    urls = []
    if engine_name == "Yandex":
        yandex_robot(driver)
    driver.get(search_url)
    if check_for_captcha(driver):
        print(f"[WARNING] CAPTCHA detected for {engine_name}. Please solve it manually.")
        input(f"Press Enter after solving the CAPTCHA for {engine_name}...")
    current_page = 0
    while current_page < no_of_pages:
        current_page += 1
        print(f"[INFO] Scraping page {current_page} of {engine_name}...")
        if engine_name == "Yandex":
            yandex_robot(driver)
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except Exception as e:
            print(f"[ERROR] Error waiting for element on {engine_name} page {current_page}: {e}")
            break
        links = driver.find_elements(By.XPATH, xpath)
        for link in links:
            url = link.get_attribute('href')
            if url:
                urls.append((url, engine_name))
        if current_page < no_of_pages:
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, next_button_xpath))
                )
                driver.execute_script("arguments[0].click();", next_button)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, xpath)))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"[ERROR] Error clicking next button for {engine_name}: {e}")
                print("No next button found, or it's the last page.")
                break
    driver.quit()
    return urls


def url_scrapper_google(product_name, no_of_pages):
    driver = get_driver()
    search_url = f"https://www.google.com/search?q={product_name}&num=10"
    return scrape_urls(driver, search_url, "Google", no_of_pages,"//div[@class='yuRUbf']//a", "//span[contains(text(), 'Next')]")


def url_scrapper_bing(product_name, no_of_pages):
    driver = get_driver()
    search_url = f"https://www.bing.com/search?q={product_name}"
    return scrape_urls(driver, search_url, "Bing", no_of_pages,"//li[@class='b_algo']//h2/a", "//a[@class='sb_pagN sb_pagN_bp b_widePag sb_bp ']")


def url_scrapper_yahoo(product_name, no_of_pages):
    driver = get_driver()
    search_url = f"https://in.search.yahoo.com/search?p={product_name}"
    return scrape_urls(driver, search_url, "Yahoo", no_of_pages,"//h3/a", "//a[@class='next' and contains(text(), 'Next')]")


def url_scrapper_yandex(product_name, no_of_pages):
    driver = get_driver()
    search_url = f"https://yandex.com/search/?text={product_name}"
    driver.get(search_url)
    if check_for_captcha(driver):
        print("Yandex bot verification detected. Attempting to bypass...")
        try:
            captcha_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//input[@id="js-button"]')))
            print("Button found, clicking...")
            driver.execute_script("arguments[0].click();", captcha_button)
            captcha_button.click()
            print("CAPTCHA clicked successfully.")
        except Exception as e:
            print("Manual verification required. Please solve the CAPTCHA.")
            input("Press Enter after solving the CAPTCHA...")
    return scrape_urls(driver, search_url, "Yandex", no_of_pages,"//a[contains(@class,'organic__url')]","//div[@class='Pager-ListItem Pager-ListItem_type_next']//a[@class='VanillaReact Pager-Item Pager-Item_type_next' and contains(text(), 'next')]")


def url_scrapper_duckduckgo(product_name, no_of_pages):
    driver = get_driver()
    search_url = f"https://duckduckgo.com/?q={product_name}&ia=web"
    return scrape_urls(driver, search_url, "DuckDuckGo", no_of_pages,"//div[@class='pAgARfGNTRe_uaK72TAD']//a","//div[@class='rdxznaZygY2CryNa5yzk']//button[@id='more-results' and contains(text(), 'More results')]")


def save_to_csv(data, filename="search_results.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["URL", "Search Engine"])
        writer.writerows(data)


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
    print("Search results CSV saved successfully!")


from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_normal_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--incognito")
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_response_code(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code
    except requests.exceptions.RequestException:
        return None


def details_scraper(url):
    driver = get_normal_driver()
    try:
        driver.set_page_load_timeout(8)
        driver.get(url)
        WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        scroll_page(driver, iterations=7, pause=3)
        print(f"[INFO] Checking download section on: {url}")
    except (TimeoutException, WebDriverException):
        print(f"[ERROR] Timeout loading {url}, skipping download check.")
        driver.quit()
        return "Timeout"
    try:
        page_source = driver.page_source.lower()
        if "verify" in page_source or "captcha" in page_source:
            print("[INFO] Detected potential verification, waiting extra...")
            time.sleep(5)
            scroll_page(driver, iterations=3, pause=2)
    except Exception:
        pass
    try:
        main_window = driver.current_window_handle
        ad_close_xpaths = [
            "//button[contains(text(), 'Close')]",
            "//div[contains(@class, 'close')]",
            "//span[contains(text(), 'X')]",
            "//button[contains(@aria-label, 'close')]",
            "//div[contains(@id, 'dismiss-button')]"
        ]
        for ad_xpath in ad_close_xpaths:
            ads = driver.find_elements(By.XPATH, ad_xpath)
            for ad in ads:
                try:
                    driver.execute_script("arguments[0].click();", ad)
                    print("[INFO] Closed an ad pop-up!")
                except Exception:
                    continue
        if len(driver.window_handles) > 1:
            for handle in driver.window_handles:
                if handle != main_window:
                    driver.switch_to.window(handle)
                    driver.close()
                    print("[INFO] Closed an ad tab!")
            driver.switch_to.window(main_window)
    except Exception as e:
        print(f"[DEBUG] Error handling pop-ups: {e}")

    # Expanded XPath list for download button detection:
    xpaths = [
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
        "(//a[contains(@class, 'accent_color') and contains(@href, 'android-apk-download')])[1]"
    ]

    for xpath in xpaths:
        try:
            button = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            href = button.get_attribute("href")
            print(f"[INFO] Download button found using: {xpath}")
            driver.quit()
            return "Yes"
        except (NoSuchElementException, TimeoutException):
            continue

    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"[DEBUG] Detected {len(iframes)} iframes, checking...")
        for index, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                for xpath in xpaths:
                    try:
                        button = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
                        href = button.get_attribute("href")
                        print(f"[INFO] Download button found inside iframe {index + 1} using: {xpath}")
                        driver.quit()
                        return "Yes"
                    except (NoSuchElementException, TimeoutException):
                        continue
                driver.switch_to.default_content()
            except Exception:
                driver.switch_to.default_content()
                continue
    except Exception as e:
        print(f"[DEBUG] Error checking iframes: {e}")

    print("[INFO] No download button found.")
    driver.quit()
    return "No"


def process_url(url, engine):
    print(f"\n[INFO] Processing URL: {url} (Engine: {engine})")
    response_code = get_response_code(url)
    download_status = details_scraper(url)
    # Skip URLs that timed out (do not include "Timeout" in CSV)
    if download_status == "Timeout":
        print(f"[INFO] Skipping URL due to timeout: {url}")
        return None
    return [url, engine, response_code, download_status]


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
    print("Search results CSV saved successfully!")


def save_to_csv(data, filename="search_results.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["URL", "Search Engine"])
        writer.writerows(data)


def main_process():
    csv_filename = "search_results.csv"
    all_results = []
    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            all_results.append((row["URL"], row["Search Engine"]))
    print(f"[INFO] {len(all_results)} URLs loaded from {csv_filename}")

    download_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(process_url, url, engine): (url, engine) for url, engine in all_results}
        for future in concurrent.futures.as_completed(future_to_url):
            url, engine = future_to_url[future]
            try:
                result = future.result()
            except Exception:
                result = None
            if result is not None:
                download_results.append(result)

    output_filename = "download_results.csv"
    with open(output_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["URL", "Search Engine", "HTTP Response", "Download Button"])
        writer.writerows(download_results)
    print(f"[INFO] Download results CSV saved successfully as {output_filename}")


def main():
    print("Step 1: Collecting Links")
    main_collect()
    print("\nStep 2: Processing Links")
    main_process()


if __name__ == "__main__":
    main()
