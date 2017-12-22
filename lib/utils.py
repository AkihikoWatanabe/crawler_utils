# coding=utf-8

from time import sleep
import numpy.random as random 
from urllib.parse import urlparse 
from retrying import retry
import requests
import cchardet
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
import timeout_decorator

import crawler.lib.const as GC
import internet_archives.lib.const as C
import internet_archives.lib.custom_conditions as cec

class Queue:
    
    def __init__(self, queue=None, max_size=5):

        if type(queue) is type([]):
            self.queue = queue
        elif queue is None:
            self.queue = []

        self.max_size = max_size

    def enqueue(self, e):

        self.queue.append(e)
        return self.queue

    def dequeue(self):
        
        elem = self.queue[0]
        del self.queue[0]

        return elem

    def is_full(self):

        return len(self.queue) >= self.max_size

    

def random_sleep(max_sleep_time):
    """ 1 - max_sleep_timeの間でランダムにsleepをはさむ関数

    Args:
        max_sleep_time (int): sleepをはさむ最大秒数
    """

    sleep(random.choice(range(max_sleep_time)))
    #sleep(max_sleep_time)


def normalize_url(url, source_url):
    """ スクレイピングしたurlを正規化する関数
    
    //hogehoge.com -> http://hogehoge.com
    /article.com -> http://hogehoge.com/article.com
    ?page=2 -> http://hogehoge.com/article?page=2

    Args:
        url (str): スクレイピングしたurl
        source_url (str): スクレイピング元のurl

    Returns:
        str: 正規化されたurl文字列

    """

    parsed_url = urlparse(source_url)
    if url[:2] == "//":
        return "{}:{}".format(parsed_url.scheme, url)
    elif url[:1] == "/":
        return "{}://{}{}".format(parsed_url.scheme, parsed_url.netloc, url)
    elif url[:1] == "?":
        return "{}://{}{}{}".format(parsed_url.scheme, parsed_url.netloc, parsed_url.path, url) 
    return url  


def status_code2str(status_code):

    if status_code >= 500 and status_code <= 520:
        return GC.SERVER_ERROR
    elif status_code >= 400 and status_code <= 451:
        return GC.CLIENT_ERROR
    elif status_code >= 300 and status_code <= 310:
        return GC.REDIRECTION
    elif status_code >= 200 and status_code <= 226:
        return GC.SUCCESS
    elif status_code >= 100 and status_code <= 102:
        return GC.INFORMATIONAL 


@timeout_decorator.timeout(GC.TIMEOUT, timeout_exception=TimeoutError)
def get(url, logger, sleep_time, use_selenium=False, is_ia=False):
        """ urlにGETリクエストを送り、htmlを取得する

        Args:
            url (str): GETリクエストを送るurl
            logger (logger): loggerインスタンス
            use_selenium (bool): seleniumを使用するか否か

        Returns:
            Responce: HttpResponce　取得できなければNone
        """

        @retry(
                stop_max_attempt_number=GC.STOP_MAX_ATTEMPT_NUMBER,
                stop_max_delay=GC.STOP_MAX_DELAY,
                wait_fixed=GC.WAIT_FIXED
        )
        def __get(url):
            return requests.get(url, headers=GC.HEADERS, timeout=GC.TIMEOUT)

        try:
            res = __get(url)
        except Exception as e:
            logger.error("requests exception {}".format(e))
            raise TimeoutError

        encoding = cchardet.detect(res.content)['encoding'].lower() 
        res.encoding = encoding
        status_str = status_code2str(res.status_code)
        if status_str in [GC.SERVER_ERROR, GC.CLIENT_ERROR, GC.REDIRECTION]:  # ニュースサイト等のリダイレクトはたいていトップページへ飛ばされるだけ 
            logger.warning(
                    "{}: status_code {} on {}".format(status_str, res.status_code, url)
            ) 
            random_sleep(sleep_time)
            return None, res.status_code
        elif status_str in [GC.INFORMATIONAL]:
            logger.info(
                    "{}: status_code {} on {}".format(status_str, res.status_code, url)
            )
        
        if use_selenium:
            dcap = {
                    "phantomjs.page.settings.userAgent": GC.HEADERS,
                    "marionette": True
            }
            args = [
                    "--ignore-ssl-errors=true",
                    "--ssl-protocol=any",
                    "--disk-cache=false",
                    "--load-images=false",
                    "--output-encoding=utf-8",
                    "--script-encoding={}".format(encoding)
            ]
            try:
                driver = webdriver.PhantomJS(desired_capabilities=dcap, service_args=args)
                # GET
                driver.set_page_load_timeout(GC.TIMEOUT)
                driver_wait = WebDriverWait(driver, GC.TIMEOUT)
                driver.get(url)
                if is_ia:
                    driver_wait.until(
                            cec.visibility_of_multiple_element_located(
                                    (By.CSS_SELECTOR, C.TARGET_ERROR_CSS_SELECTOR),
                                    (By.CSS_SELECTOR, C.TARGET_LINK_CSS_SELECTOR)
                            )
                    )
                else:
                    driver_wait.until(ec.presence_of_all_elements_located)
                html = driver.page_source
            except TimeoutException:
                logger.error("selenium TimeoutException on {}".format(url))
                random_sleep(sleep_time)
                raise TimeoutError
            except Exception as e:
                logger.error("selenium {} on {}".format(e, url))
                raise TimeoutError

            random_sleep(sleep_time)
            
            if driver.current_url != url:
                logger.warning(
                        "selenium redirect on {} but html has saved on db.".format(url)
                )
                driver.close()
                return html, GC.SELENIUM_REDIRECT
            else:
                driver.close()
                return html, res.status_code
        else:
            random_sleep(sleep_time)
            return res.text, res.status_code
