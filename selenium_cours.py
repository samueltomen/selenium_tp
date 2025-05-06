import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get("https://doctolib.fr")

wait = WebDriverWait(driver, 10)

wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input")))

place_input = wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input")))

place_input.clear()
place_input.send_keys("75005")

wait.until(ec.text_to_be_present_in_element_value((By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input"), "75005"))
place_input.send_keys(Keys.ENTER)
time.sleep(10)
total_results = driver.find_element(By.CSS_SELECTOR, "div[data-test='total-number-of-results']")

time.sleep(50)