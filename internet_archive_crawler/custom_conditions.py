# coding=utf-8

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException


class visibility_of_multiple_element_located(object):
    
    def __init__(self, locator1, locator2):
        self.locator1 = locator1
        self.locator2 = locator2

    def __call__(self, driver):
        try:
            return _element_if_visible(_find_element(driver, self.locator1))
        except NoSuchElementException:
            return _element_if_visible(_find_element(driver, self.locator2))
        except StaleElementReferenceException:
            return False

def _element_if_visible(element, visibility=True):
    return element if element.is_displayed() == visibility else False

def _find_element(driver, by):
    try:
        return driver.find_element(*by)
    except WebDriverException as e:
        raise e
