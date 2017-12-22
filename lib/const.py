# coding=utf-8

SLEEP_TIME = 4
TIMEOUT = 60  #  タイムアウトにしようする秒数
RECALL_THR = 0.5 

MAX_QUEUE_SIZE = 5

MAX_PAGES = 10

HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
} 

# httpレスポンス　ステータスコードを表す文字列
SERVER_ERROR = "Server Error"
CLIENT_ERROR = "Client Error"
REDIRECTION = "Redirection"
SUCCESS = "Success"
INFORMATIONAL = "Informational"  

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ステータスコード(HTTP Responceのステータスコードに便宜上追加)
TIMEOUT_SEARCH_DISPURL = 521  # 続きを読むリンクの探索がタイムアウトした場合のステータスコード
TIMEOUT_SEARCH_NEXTURL = 522  # 次のページリンクの探索がタイムアウトした場合のステータスコード
SELENIUM_REDIRECT = 310  # seleniumがページ読み終わったときリダイレクトしてた場合
TIMEOUT = 520  # 接続がタイムアウトなどした場合
REDIRECT_TOP_PAGES = 600
TOO_MANY_SERVER_OR_CLIENT_ERROR = 601

# GETで例外が発生したときにリトライする回数
STOP_MAX_ATTEMPT_NUMBER = 5 
STOP_MAX_DELAY = 10000  # リトライする時間は最大10秒間
WAIT_FIXED = 2000  # リトライする際は2秒間隔で

# 次ページへのリンク、続きを読むリンクを検出するためのパターン
URL_PAT = "(:?http)?s?:?/?[/|\?][\w/:%#\$&\?\(\)~\.=\+\-]+"
OPEN_BRACKETS_PAT = "[\[|\(|（|「|【|『|《|〈|〔|｛|\{|<|&lt;|&laquo;]"
CLOSED_BRACKETS_PAT = "[\]|\)|）|」|】|』|》|〉|〕|｝|\}|>|&gt;|&raquo;]" 
LINK_GROUP_NAME = "link"
LINK_PAT = "<a [^>]*?href=[\"|'](?P<{link}>{url})[\"|'][^>]*?>(?:<span\s?[^>]*?>)?{open_brackets}?{atext}{closed_brackets}?(?:</span>)?</a>"
