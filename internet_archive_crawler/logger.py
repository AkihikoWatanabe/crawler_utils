# coding=utf-8

"""
logging機能を提供するモジュール
"""

import os
import logging
from internet_archives.lib.const import LOG_DIR


def get_logger(file_name, logger_name="hogehogeLogger"):
    """ loggerインスタンスを取得する

    Args:
        file_name (str): logを出力するファイル名
        logger_name (str): logの出力名

    Returns:
        logger.Logger: フォーマット、出力名、出力ファイルが指定されたlogger
    """

    logger = logging.getLogger(logger_name)
    handler = logging.FileHandler(
            os.path.join(LOG_DIR, "{}.log".format(file_name))
    )
    formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger
