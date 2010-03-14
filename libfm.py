__all__ = ['LibFM']

# The last.fm API schema. Proxy objects are generated based on this
API_SCHEMA = {
    'artist' : {
            'getInfo' : (('artist', False))
        },
    'user' : {
            'getRecentTracks' : (('user', True))
        },
    }

class Proxy(object):
    """Base proxy class"""
    
    def __init__(self, client, name):
        self._client = client
        self._name = name

    def __call__(self, method):
        return self._client('%s.%s' % (self._name, method))

def _generate_proxies():
    """Generate proxy metaclasses for API namespaces."""
    
    for namespace in API_SCHEMA:
        methods = {}
        for method in API_SCHEMA[namespace]:
            body = ['def %s(self):' % method]
            body.append('   return self("%s")' % method)
            exec('\n'.join(body))
            methods[method] = eval(method)
        proxy = type('%sProxy' % namespace.title(), (Proxy, ), methods)
        globals()[proxy.__name__] = proxy

_generate_proxies()

class ArtistProxy(ArtistProxy):
    """Example proxy class for artist namespace."""
    
    def getInfo(self):
        """An overriden method."""
        
        return "custom getInfo"

class LibFM(object):
    """Provides access to last.fm API."""

    def __init__(self, api_key):
        self._api_key = api_key
        self._http_client = _HttpClient()
        
        for namespace in API_SCHEMA:
            self.__dict__[namespace] = eval('%sProxy(self, "%s")' \
                            % (namespace.title(), namespace))

    def __call__(self, name, params=None):
        """Handle standard API methods."""
        
        return "do it all: %s" % name

if __name__ == '__main__':
    # TODO: moves these to a unit test
    libFM = LibFM("b25b959554ed76058ac220b7b2e0a026")
    print libFM.artist.getInfo()
    print libFM.user.getRecentTracks()
