# coding=utf-8

from bs4 import BeautifulSoup
from tqdm import tqdm
from time import sleep

from internet_archives.models import Url, PageUrl, Source
from django.db import transaction

import crawler.lib.utils as global_utils
from crawler.lib.container import ScrapedArticleData
import crawler.lib.const as GC
import crawler.lib.page_navigator as navi
import internet_archives.lib.const as C

class InternetArchivesCrawler():

    def __init__(self, sleep_time=1):

        self.TARGET_INFO = [l.strip().split("|||")[:3]
                for l in open(C.CRAWLING_TARGET_FILE).read().strip().split("\n")]
        self.SLEEP_TIME = sleep_time

    def __scrape_archives(self, url, logger):
        """ InternetArchive上のページから、htmlが格納されているリンクを取得する
        
        Args:
            url (str): Internet Archives上のキャッシュにアクセスしたいurl
            logger (logger): loggerインスタンス
        Returns:
            str: Internet Archives上のキャッシュにアクセスできるURL
        """

        # 既にスクレイピングしたか否か確認
        try:
            Url.objects.get(url_string=url)
            return None
        except:
            pass  # スクレイピングされていなければスクレイピング処理

        ia_url = "{}{}".format(C.IA_PREFIX.strip(), url.strip())
        try:
            html, status_code = global_utils.get(
                    ia_url,
                    logger,
                    self.SLEEP_TIME,
                    use_selenium=True,
                    is_ia=True
            )
            soup = BeautifulSoup(html, "html.parser")
            atcl_url = soup.find("div", id=C.TARGET_LINK_ID).a.get("href")
            atcl_url = global_utils.normalize_url(atcl_url, ia_url)
            logger.info("Internet Archive has cashe for {} at {}".format(url, atcl_url))
            return atcl_url
        except TimeoutError:
            logger.error("Internet Archive Server is down.") 
            raise Exception("Internet Archive Server is down.")
        except AttributeError:
            logger.info("There is no cache of {} on internet archive. [Skip]".format(url))
            return None
        
    def __scrape_atcl(self, url, title, published_at, logger):
        """ 記事のhtmlを取得する

        次ページへのリンクがあった場合は、それらも取得

        Args:
            url (str): 収集する記事のurl
            title (str): 収集する記事のタイトル
            published_at (str): 収集する記事がceronに登録された日付
            logger (logger): loggerインスタンス

        Returns:
            list: ScrapedArticleDataのリスト、クライアント・サーバエラーやリダイレクトされた場合はNoneを返す
        """

        page_ctr, origin_url, atcl_list = 1, url, []
        while True:
            try:
                html, status_code = global_utils.get(
                        url,
                        logger,
                        self.SLEEP_TIME,
                        use_selenium=True
                )
            except TimeoutError:
                atcl_list.append(
                        ScrapedArticleData(
                            origin_url,
                            url,
                            title,
                            '',
                            page_ctr,
                            published_at,
                            GC.TIMEOUT
                        )
                )
                return atcl_list 
            # レスポンスでエラーや404だった場合はhtmlは格納しない
            if global_utils.status_code2str(
                    status_code) in [GC.SERVER_ERROR, GC.CLIENT_ERROR]:
                atcl_list.append(
                        ScrapedArticleData(
                            origin_url,
                            url,
                            title,
                            '',
                            page_ctr,
                            published_at,
                            status_code
                        )
                )
                return atcl_list

            # 全文表示へのリンクがあるか否か
            try:
                disp_url = navi.search_dispurl(html)
            except TimeoutError:
                logger.warning(
                        "TimeoutError at search_dispurl on {}. [SKIP]".format(url)
                )
                return atcl_list.append(
                        ScrapedArticleData(
                            origin_url,
                            url,
                            title,
                            html,
                            page_ctr,
                            published_at,
                            GC.TIMEOUT_SEARCH_DISPURL
                        )
                )
            if disp_url:
                logger.info("disp_url exists at {}: {}".format(url, disp_url))
                url = global_utils.normalize_url(disp_url, url)
                html, status_code = global_utils.get(url, logger, self.SLEEP_TIME, use_selenium=True)
                if global_utils.status_code2str(
                    status_code) in [GC.SERVER_ERROR, GC.CLIENT_ERROR]:
                    atcl_list.append(
                        ScrapedArticleData( 
                            origin_url,
                            url,
                            title,
                            '',
                            page_ctr,
                            published_at,
                            status_code
                        )
                    )
                    return atcl_list 

            atcl_list.append(
                    ScrapedArticleData(
                        origin_url,
                        url,
                        title,
                        html,
                        page_ctr,
                        published_at,
                        status_code
                    )
            )
            try:
                next_url = navi.search_nexturl(html, page_ctr)
            except TimeoutError:
                logger.warning(
                        "TimeoutError at search_nexturl on {}. [SKIP]".format(url)
                )
                atcl_list[-1] = ScrapedArticleData(
                        origin_url,
                        url,
                        title,
                        html,
                        page_ctr,
                        published_at,
                        GC.TIMEOUT_SEARCH_NEXTURL
                )
                return atcl_list  
            if navi.is_next_url(next_url, origin_url): 
                page_ctr += 1
                if page_ctr > GC.MAX_PAGES:
                   logger.warning("{} has too many pages. {} pages".format(url, page_ctr))
                   break
                url = global_utils.normalize_url(next_url, origin_url)
            else:
                break

        return atcl_list 

    @transaction.atomic
    def __save(self, url, atcl_list):
        
        url, created = Url.objects.get_or_create(
                url_string=url,
        ) 
        if created:
            for atcl in atcl_list:
                purl, _ = PageUrl.objects.get_or_create(
                        url=url,
                        pageurl_string=atcl.page_url,
                        page=atcl.page,
                        status_code=atcl.status_code
                )
                Source.objects.get_or_create(
                        purl=purl,
                        title=atcl.title,
                        html=atcl.html,
                        published_at=atcl.published_at
                )

    def parse(self, logger):

        idx = 0
        pbar = tqdm(total=len(self.TARGET_INFO))
        while idx < len(self.TARGET_INFO):
            (url, title, published_at) = self.TARGET_INFO[idx]
            try:
            	atcl_url = self.__scrape_archives(url, logger)
            	if atcl_url == None:
            	    atcl_list = [
            	            ScrapedArticleData(
            	                url,
            	                url,
            	                title,
            	                '',
            	                1,
            	                published_at,
            	                404
            	            )
            	    ]
            	else:
            	    atcl_list = self.__scrape_atcl(atcl_url, title, published_at, logger)
            	    logger.info("{} has {} pages (Internet Archives at {}).".format(url, len(atcl_list), atcl_url))
            except Exception as e: 
                logger.info("Reconnect to internet archives after {}s by Exception: {}".format(C.IA_DELAY, e))
                sleep(C.IA_DELAY)
                continue
            self.__save(url, atcl_list)

            idx += 1
            pbar.update(1)
        pbar.close()
