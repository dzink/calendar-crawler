from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from time import sleep
from CalendarLogger import logger

import os.path

class CalendarSource:
    events = []
    driver = None

    def __init__(self, url, id = '', remote = True):
        self.url = url
        if (id == ''):
            id = url
        self.id = id
        self.remote = remote
        self.scrollCount = 0

    """
    Build and return a headless web driver.
    The driver is a class variable so each source instance will share a driver.
    """
    def getDriver(self):
        if (self.driver == None):
            chromeOptions = Options()
            chromeOptions.add_argument("--headless")
            chromeOptions.add_argument("--window-size=1920x1080")
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), chrome_options = chromeOptions, executable_path='/usr/bin/google-chrome')
            logger.debug('built chrome driver')
        return self.driver

    def getHtml(self):
        logger.info('retrieving ' + self.url)
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
    def scrollPage(self, driver, pause = 2):
        if (self.scrollCount):
            for i in range(self.scrollCount):
                driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
                sleep(pause)
