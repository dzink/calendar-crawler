import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from CalendarLogger import logger

import os.path
import subprocess
import re

class Fetcher:
    driver = None

    def __init__(self, sourceId, config, remote=True, globalConfig=None):
        self.sourceId = sourceId
        self.url = config.get('url')
        self.method = config.get('method', 'dynamic')
        self.headers = config.get('headers', {})
        self.waitFor = config.get('waitFor')
        self.scrollCount = config.get('scrollCount', 0)
        self.remote = remote
        self.globalConfig = globalConfig or {}

    def getHtml(self):
        logger.debug('retrieving ' + self.url)
        if self.remote:
            if self.method == 'static':
                return self.getStaticHtml()
            else:
                return self.getDynamicHtml()
        else:
            return self.getLocalHtml()

    def getStaticHtml(self):
        response = requests.get(self.url, headers=self.headers)
        response.raise_for_status()
        html = response.text

        with open(self.cacheFilename(), 'w') as f:
            f.write(html)

        logger.debug('retrieved static page source for ' + self.url)
        return html

    def getDynamicHtml(self):
        driver = self.getDriver()
        wait = WebDriverWait(driver, 2)
        driver.get(self.url)
        get_url = driver.current_url
        wait.until(EC.url_to_be(self.url))

        if self.waitFor:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.waitFor))
            )

        self.scrollPage(driver)

        if get_url == self.url:
            page_source = driver.page_source

        with open(self.cacheFilename(), 'w') as f:
            f.write(page_source)

        logger.debug('retrieved dynamic page source for ' + self.url)
        return page_source

    def getLocalHtml(self):
        with open(self.cacheFilename(), 'r') as f:
            page_source = f.read()
        logger.debug('retrieved local page source for ' + self.url)
        return page_source

    def cacheFilename(self):
        return 'source_html/page_source__' + self.sourceId + '.html'

    def getDriver(self):
        if Fetcher.driver is None:
            logger.debug('building chrome driver')
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--window-size=1920x1080")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            chromeBinaryLocation = self.globalConfig.get('chromeBinaryLocation')
            if chromeBinaryLocation:
                logger.debug('setting chrome binary location to ' + chromeBinaryLocation)
                options.binary_location = chromeBinaryLocation
            driverLocation = self.globalConfig.get('chromeDriverLocation')
            if driverLocation:
                service = Service(executable_path=driverLocation)
            else:
                driver_version = self.detectChromeVersion()
                service = Service(ChromeDriverManager(driver_version=driver_version).install())
            Fetcher.driver = webdriver.Chrome(service=service, options=options)
            logger.debug('built chrome driver')
        return Fetcher.driver

    def detectChromeVersion(self):
        binary = self.globalConfig.get('chromeBinaryLocation') or 'google-chrome'
        try:
            output = subprocess.check_output([binary, '--version'], stderr=subprocess.DEVNULL).decode().strip()
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', output)
            if match:
                version = match.group(1)
                logger.debug('detected chrome version: ' + version)
                return version
        except Exception as e:
            logger.debug('could not detect chrome version: ' + str(e))
        return None

    @staticmethod
    def quitDriver():
        if Fetcher.driver:
            logger.debug('quitting chrome driver')
            Fetcher.driver.quit()
            Fetcher.driver = None

    def scrollPage(self, driver, pause=2):
        if self.scrollCount:
            for i in range(self.scrollCount):
                driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
                sleep(pause)
