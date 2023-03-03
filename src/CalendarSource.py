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

    def __init__(self, url, source_id = '', remote = True):
        self.url = url
        if (source_id == ''):
            source_id = url
        self.source_id = source_id
        self.remote = remote
        self.scrollCount = 0

    def getDriver(self):
        """
        Build and return a headless web driver.
        The driver is a class variable so each source instance will share a driver.
        """
        if (self.driver is None):
            chromeOptions = Options()
            chromeOptions.add_argument("--headless")
            chromeOptions.add_argument("--window-size=1920x1080")
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                chrome_options = chromeOptions, executable_path='/usr/bin/google-chrome')
            logger.debug('built chrome driver')
        return self.driver

    def getHtml(self):
        """
        Get the HTML, either remotely or from a local file.
        This functionality is set from the command line.
        """

        logger.info('retrieving ' + self.url)
        # I think the else improves readability.
        # pylint: disable=no-else-return

        if (self.remote):
            return self.getRemoteHtml()
        else:
            html = self.getLocalHtml()
            self.write_local_html(html)
            return html

    def getRemoteHtml(self):
        """ Get a webdriver and get the remote HTML. """

        driver = self.getDriver()
        wait = WebDriverWait(driver, 2)
        driver.get(self.url)
        get_url = driver.current_url
        wait.until(EC.url_to_be(self.url))
        self.scrollPage(driver)

        if get_url == self.url:
            page_source = driver.page_source

        logger.debug('retrieved remote page source for ' + self.url)
        return page_source

    def write_local_html(self, html):
        """ Store the html from a remote source pull for faster re-running. """
        with open(self.local_html_filename(), 'w') as token:
            token.write(html)

    def getLocalHtml(self):
        """ Get the stored local HTML from the last remote pull. """
        page_source = ''
        with open(self.local_html_filename(), 'r') as token:
            page_source = token.read()
            token.close()
        logger.debug('retrieved local page source for ' + self.url)
        return page_source

    def local_html_filename(self):
        """ Helper to make building the local filename easier. """
        return 'source_html/page_source__' + self.source_id + '.html'

    def setScrollCount(self, scrollCount):
        """
        Indicate how many times the page should be scrolled.
        Useful for pages that auto-load more events.
        Set this before getting the source.
        """
        self.scrollCount = scrollCount

    def scrollPage(self, driver, pause = 2):
        """ Some sources need to be scrolled to find all events. This does that. """
        if (self.scrollCount):
            for _ in range(self.scrollCount):
                driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
                sleep(pause)
