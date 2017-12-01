# coding=utf-8

# timeout-decoratorを使えばよい

from functools import wraps

def on_timeout(limit, handler, hint=None):
    '''
    指定した実行時間に終了しなかった場合、handlerをhint/limitを引数にして呼び出します
    @on_timeout(limit=3600, handler=notify_func, hint=u'calculation')
    def long_time_function():
    '''

    def notify_handler(signum, frame):
        handler("WARNING: {} is not finished in {} seconds.".format(hint, limit))

    def __decorator(function):
        def __wrapper(*args, **kwargs):
            import signal
            signal.signal(signal.SIGALRM, notify_handler)
            signal.alarm(limit)
            result = function(*args, **kwargs)
            signal.alarm(0)
            return result
        return wraps(function)(__wrapper)
    return __decorator 
