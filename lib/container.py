# coding=utf-8

from collections import namedtuple

# 記事の情報を格納するnamedtuple
ScrapedArticleData = namedtuple(
    'ScrapedArticleData',
    ('origin_url', 'page_url', 'title', 'html', 'page', 'published_at', 'status_code')
)

class ScrapedArticleDataWithDocstring(ScrapedArticleData):
    """ Scrapingしたデータを格納するnamedtuple

    Attributes:
        origin_url (str): 元記事の1ページ目のurl
        page_url (str): 元記事のnページ目のurl
        title (str): 元記事のタイトル
        html (str): 元記事のhtmlソース
        page (int): 参照している元記事のページ番号
        published_at (datetime): ceron上に記事が登録されたdatetime
        status_code (int): レスポンスのステータスコード
    """  
