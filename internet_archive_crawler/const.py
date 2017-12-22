# coding=utf-8

import os

IA_DELAY = 60
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CRAWLING_TARGET_FILE = os.path.join(BASE_DIR, "lib", "crawling_target")
IA_PREFIX = "https://web.archive.org/web/*/"

TARGET_ERROR_CSS_SELECTOR = "div.error.error-border"
TARGET_LINK_CSS_SELECTOR = "div#wb-meta"
TARGET_LINK_ID = "wb-meta"

# logを格納するディレクトリ
LOG_DIR = os.path.join(BASE_DIR, "log")
