# coding=utf-8

import re
from crawler.lib.timeout import on_timeout 
from difflib import SequenceMatcher
import crawler.lib.const as GC


def is_next_url(next_url, item_link):
    """ next_urlが次ページへのリンクか否かを判定する

    判定をする際は、次ページリンク候補の文字列(next_url)と、スクレイピング元urlの文字列(item_link)の比較を行い、
    item_link中に含まれるnext_urlの割合, i.e. recall が0.5以上であれば次ページへのリンクとみなす
        http://youtube.com, http://hogehoge.com -> False
        http://hogehoge.com/article, http://hogehoge.com -> True
        http://hogehoge.com/article/1234/5678, /article/1234/5678?page=2 - > True 

    例外として、next_urlがitem_linkと比較して#がinsertされている場合のみはアンカなのでFalseを返す
        http://hogehoge.com/article#overview, http://hogehoge.com/article

    また、next_urlが?から始まるパラメータの場合は、Trueを返す
    このとき、ドメインが一致していない場合はFalseとなる
        http://hogehoge.com/article, http://hogehoge.com/article?page=2 -> True
        http://hogehoge.com/article, ?page=2 -> True
        http://hogehoge.com/article, http://youtube.com/article?page=2 -> False

    

    Args:
        next_url (str): 次ページへのリンク候補
        item_link (str): スクレイピング元のurl

    Returns
        bool: 次ページへのリンクだった場合はTrue、そうでない場合はFalse
    """

    TAG = 0
    SEQ1_START = 1
    SEQ1_END = 2 

    def is_anchor(m):
        
        opcodes = m.get_opcodes()
        if opcodes[-1][TAG] == "delete":  # ページ内リンクの場合は末尾がdelete
            start = opcodes[-1][SEQ1_START]
            end = opcodes[-1][SEQ1_END]
            if opcodes[-1][start:end][:1] == "#":
                return True
        return False

    def is_param(m, cand):

        if cand[:1] == "?":
            return True
        opcodes = m.get_opcodes()
        if opcodes[-1][TAG] == "delete":
            start = opcodes[-1][SEQ1_START]
            end = opcodes[-1][SEQ1_END]
            if opcodes[-1][start:end][:1] == "?":
                return True 
        return False

    def calc_recall(m, whole_len):

        # 一致する部分の長さを求める
        matched_len = sum([opcode[SEQ1_END] - opcode[SEQ1_START]
                for opcode in m.get_opcodes() if opcode[TAG] == "equal"])

        return float(matched_len) / whole_len

    if next_url == None:
        return False

    matcher = SequenceMatcher()
    matcher.set_seq1(next_url)
    matcher.set_seq2(item_link)

    # ページ内リンクの場合
    if is_anchor(matcher):
        return False
    # パラメータを与えるリンクの場合
    if is_param(matcher, next_url):
        return True
    # 部分一致文字列からnext_urlのrecall計算し一定値以上なら
    # 次ページへのリンクとする
    if calc_recall(matcher, len(next_url)) >= RECALL_THR:
        return True

    return False  


def get_nextpat():
    """ クローリングしている記事が複数ページにまたがっているか否か判定する正規表現を返す

    クローリングしている記事が「次のページ」等のリンクによって複数ページにまたがっているかを判定する正規表現を返す

    Returns:
       re.pattern: 次ページリンクがあるか否か判定する正規表現パターン 
    """

    next_pat = re.compile(
            GC.LINK_PAT.format(
                link=GC.LINK_GROUP_NAME,
                url=GC.URL_PAT,
                atext="(?:次のページ|次へ|次ページ)",
                open_brackets=GC.OPEN_BRACKETS_PAT,
                closed_brackets=GC.CLOSED_BRACKETS_PAT
            )
    ) 

    return next_pat


def get_nextpat_by_pagectr(ctr):
    """ クローリングしている記事が複数ページにまたがっているか否か判定する正規表現を返す

    クローリングしている記事が「1 2」等のリンクによって複数ページにまたがっているかを判定する正規表現を返す

    Args:
        ctr (int): 現在参照しているページのページ番号
    Returns:
        re.pattern: 次ページリンクがあるか否か判定する正規表現パターン  
    """ 

    next_pat = re.compile(
            GC.LINK_PAT.format(
                link=GC.LINK_GROUP_NAME, 
                url=GC.URL_PAT,
                atext=str(ctr + 1),
                open_brackets=GC.OPEN_BRACKETS_PAT,
                closed_brackets=GC.CLOSED_BRACKETS_PAT
            )
    )

    return next_pat


def get_disppat():
    """ クローリングしている記事が全文表示になっているか否かを判定する正規表現を返す

    Returns:
       re.pattern: 続きを読むリンクがあるか否か判定する正規表現パターン   
    """ 

    disp_pat = re.compile(
            GC.LINK_PAT.format(
                link=GC.LINK_GROUP_NAME, 
                url=GC.URL_PAT,
                atext="(?:記事全文を表示する|全文を表示する|全文を表示|続きを読む)",
                open_brackets=GC.OPEN_BRACKETS_PAT,
                closed_brackets=GC.CLOSED_BRACKETS_PAT
            )
    )

    return disp_pat


def handler_func(msg):
    """ on_timeoutの際にハンドラが呼び出す関数
    """
    print(msg, flush=True)
    raise TimeoutError


@on_timeout(limit=10, handler=handler_func, hint="search_url")
def search_url(p, html):
    """ 与えられたパターンにマッチする文字列がhtmlにあるか否か判定、group_nameで指定した要素を返す

    もっぱら、次ページへのリンクや続きを読むリンクなどの検出に用いる

    Args:
        p (re.pattern): 検出するための正規表現
        html (str): htmlの生テキスト

    Returns:
       str: 検出したパターン、検出されなかった場合はNoneを返す
    """
    
    m = p.search(html)
    if m != None:
        url = m.group(GC.LINK_GROUP_NAME)
        return url

    return None


def search_dispurl(html):
    """ 「続きを読む」などのリンクがあるか否か検出し、存在した場合はそのurlを返す

    Args:
        html (str): htmlの生テキスト

    Returns:
        str: url文字列、検出されなかった場合はNone
    """

    disp_pat = get_disppat()
    url = search_url(disp_pat, html)
    if url != None:
        return url
    return None


def search_nexturl(html, page_cnt):
    """ 「次ページへ」などのリンクがあるか否か検出し、存在した場合はそのurlを返す

    Args:
        html (str): htmlの生テキスト
        page_cnt (int): 現在参照しているページのページ番号（>=1）

    Returns:
        str: url文字列、検出されなかった場合はNone
    """

    # 次へ　などの文言から次ページ取得
    next_pat = get_nextpat()
    # "2" などの文言から次ページ取得
    next_pat_by_ctr = get_nextpat_by_pagectr(page_cnt)

    url = search_url(next_pat, html)
    if url != None and url[:1] != "#": # #から始まるものはアンカなのでスキップ
        return url 
    
    url = search_url(next_pat_by_ctr, html)
    if url != None:
        return url  

    return None 
