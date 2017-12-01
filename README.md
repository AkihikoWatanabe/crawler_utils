# crawler_utils
日本語のニュースサイトのクローラをサポートするためのライブラリ群です。

* const.py: ライブラリが使用する定数が格納されている
* timeout.py: タイムアウトデコレータ
* page\_navigateor.py: 参照しているニュース記事中に「次ページへのリンク」あるいは「全文表示のためのリンク」等があるかを検出する関数など
* utils.py: requestsとseleniumを利用しGETリクエストを送る関数など
