from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from time import sleep
from CalendarLogger import logger

import os.path
import subprocess
import re

class CalendarSource:
    events = []
    driver = None
    driverLocation = ""

    def __init__(self, url, id = '', remote = True, driverLocation = None, chromeBinaryLocation = None):
        self.url = url
        if (id == ''):
            id = url
        self.id = id
        self.remote = remote
        self.scrollCount = 0
        self.driverLocation = driverLocation
        self.chromeBinaryLocation = chromeBinaryLocation

    """
    Build and return a headless web driver.
    The driver is a class variable so each source instance will share a driver.
    """
    def getDriver(self):
        if (CalendarSource.driver == None):
            logger.debug('building chrome driver')
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--window-size=1920x1080")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            if self.chromeBinaryLocation:
                logger.debug('setting chrome binary location to ' + self.chromeBinaryLocation)
                options.binary_location = self.chromeBinaryLocation
            logger.debug('installing chrome driver')
            logger.debug('starting chrome driver service')
            if self.driverLocation:
                service = Service(executable_path=self.driverLocation)
            else:
                driver_version = self.detectChromeVersion()
                service = Service(ChromeDriverManager(driver_version=driver_version).install())
            logger.debug('starting chrome driver')
            CalendarSource.driver = webdriver.Chrome(service=service, options=options)
            logger.debug('built chrome driver')
        return CalendarSource.driver

    def detectChromeVersion(self):
        binary = self.chromeBinaryLocation or 'google-chrome'
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

    def getHtml(self):
        logger.debug('retrieving ' + self.url)
        if (self.remote):
            return self.getRemoteHtml()
        else:
            return self.getLocalHtml()

    def getRemoteHtml(self):
        driver = self.getDriver()
        wait = WebDriverWait(driver, 2)
        driver.get(self.url)
        get_url = driver.current_url
        wait.until(EC.url_to_be(self.url))
        self.scrollPage(driver)

        if get_url == self.url:
            page_source_was = ''
            page_source = driver.page_source

        with open(self.pageSourceFilename(), 'w') as token:
            token.write(page_source)

        logger.debug('retrieved remote page source for ' + self.url)
        return page_source

    def getLocalHtml(self):
        page_source = ''
        with open(self.pageSourceFilename(), 'r') as token:
            page_source = token.read()
            token.close()
        logger.debug('retrieved local page source for ' + self.url)
        return page_source

    def pageSourceFilename(self):
        return 'source_html/page_source__' + self.id + '.html'

    """
    Indicate how many times the page should be scrolled.
    Useful for pages that auto-load more events.
    Set this before getting the source.
    """
    def setScrollCount(self, scrollCount):
        self.scrollCount = scrollCount

    """
    Some sources need to be scrolled to the bottom of the page before they will
    load all events.
    """
    @staticmethod
    def quitDriver():
        if CalendarSource.driver:
            logger.debug('quitting chrome driver')
            CalendarSource.driver.quit()
            CalendarSource.driver = None

    def scrollPage(self, driver, pause = 2):
        if (self.scrollCount):
            for i in range(self.scrollCount):
                driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
                sleep(pause)
