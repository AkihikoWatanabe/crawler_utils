# coding=utf-8

from time import sleep
import numpy.random as random 
from urllib.parse import urlparse 
from retrying import retry
import requests
import cchardet
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
import timeout_decorator

import crawler.lib.const as GC

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
    """ HTTP Responceステータスコードをステータスコードを表す文字列に変換する

    Args:
        status_code (int): ステータスコード

    Returns:
        str: ステータスコードを表す文字列
    """

    if status_code >= 500 and status_code <= 510:
        return GC.SERVER_ERROR
    elif status_code >= 400 and status_code <= 451:
        return GC.CLIENT_ERROR
    elif status_code >= 300 and status_code <= 308:
        return GC.REDIRECTION
    elif status_code >= 200 and status_code <= 226:
        return GC.SUCCESS
    elif status_code >= 100 and status_code <= 102:
        return GC.INFORMATIONAL 


def get_webdriver(script_encoding="utf-8"):
    """ seleniumのwebdriverを取得する

    Returns:
        webdriver.PhantomJS: PhantomJSのwebdriver
    """

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
            "--script-encoding={}".format(script_encoding)
    ] 

    return webdriver.PhantomJS(desired_capabilities=dcap, service_args=args) 

@timeout_decorator.timeout(10, timeout_exception=TimeoutError)
def get(url, logger, sleep_time, use_selenium=False):
        """ urlにGETリクエストを送り、htmlを取得する

        Args:
            url (str): GETリクエストを送るurl
            logger (logger): loggerインスタンス
            sleep_time: GETリクエストを送った際にスリープさせる最大時間
            use_selenium (bool): seleniumを使用するか否か

        Returns:
            str: 取得したhtmlの生テキスト
            int: ステータスコード
        """

        @retry(
                stop_max_attempt_number=GC.STOP_MAX_ATTEMPT_NUMBER,
                stop_max_delay=GC.STOP_MAX_DELAY,
                wait_fixed=GC.WAIT_FIXED
        )
        def __GET_requests(url):
            """ 引数で与えられたurlにrequestsでGETリクエストを送る

            Returns:
                Responce: HTTPResponce
            """

            return requests.get(url, headers=GC.HEADERS, timeout=GC.TIMEOUT)

        def __GET_webdriver(driver, url):
            """ 引数で与えられたurlにselenium web.driverでGETリクエストを送る

            Args:
                driver (webdriver): seleniumのweb driver
                url (str): GETリクエストを送るurl
            """

            driver.set_page_load_timeout(GC.TIMEOUT)
            driver_wait = WebDriverWait(driver, GC.TIMEOUT)
            driver.get(url)
            driver_wait.until(ec.presence_of_all_elements_located) 

        try:
            res = __GET_requests(url)
        except Exception as e:
            logger.error("{}".format(e))
            raise TimeoutError

        def __is_redirect(current_url, origin_url):
            """ リダイレクトしたか否かを判定
            """

            if current_url != origin_url:
                return True
            return False

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
            
            try:
                driver = __GET_webdriver(script_encoding=encoding)
                html = driver.page_source
            except TimeoutException:
                random_sleep(sleep_time)
                raise TimeoutError

            random_sleep(sleep_time)
            
            if __is_redirect(driver.current_url, url):
                logger.warning(
                        "selenium redirect on {}".format(url)
                )
                return html, GC.SELENIUM_REDIRECT
            else:
                return html, res.status_code
        else:
            random_sleep(sleep_time)
            return res.text, res.status_code
