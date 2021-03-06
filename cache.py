# the caching decorator for helpers functions

class Cache:
    cache = {}
    previousCache = None
    item = None

    @staticmethod
    def reset():
        Cache.cache = {}

    # only used by the solver
    @staticmethod
    def addItem(item):
        Cache.previousCache = Cache.cache
        Cache.item = item
        Cache.cache = {}

    @staticmethod
    def removeItem(item):
        if item == Cache.item:
            Cache.cache = Cache.previousCache
        else:
            Cache.cache = {}
        Cache.previousCache = None
        Cache.item = None

    @staticmethod
    def decorator(func):
        def _decorator(self):
            if func.__name__ in Cache.cache:
#                print("cache found for {}: {}".format(func.__name__, Cache.cache[func.__name__]))
#                ret = func(self)
#                if ret != Cache.cache[func.__name__]:
#                    print("ERROR: cache ({}) != current ({}) for {}".format(Cache.cache[func.__name__], ret, func.__name__))
                return Cache.cache[func.__name__]
            else:
                ret = func(self)
                Cache.cache[func.__name__] = ret
#                print("cache added for {}: {}".format(func.__name__, Cache.cache[func.__name__]))
                return ret
        return _decorator

class RequestCache(object):
    def __init__(self):
        self.results = {}

    def request(self, request, *args):
        return ''.join([request] + [str(arg) for arg in args])

    def store(self, request, result):
        self.results[request] = result

    def get(self, request):
        return self.results[request] if request in self.results else None

    def reset(self):
        self.results.clear()
