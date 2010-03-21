import md5
import urllib
import urllib2

__all__ = ['LibFM']

# The last.fm API schema. Proxy objects are generated based on this
API_SCHEMA = {
    'album' : {
            'addTags' : [('artist', []),
                         ('album', []),
                         ('tags', []),
                         ('sk', []),
                ],
        },
    'artist' : {
            'getInfo' : [('artist', ['optional']),
                         ('mbid', ['optional']),
                         ('username', ['optional']),
                         ('lang', ['optional']),
                ],
            'getEvents' : [('artist', []),
                ],
        },
    'user' : {
            'getRecentTracks' : [('user', []),
                                 ('limit', ['optional']),
                                 ('page', ['optional']),
                ],
        },
    }

LIBFM_URL = 'http://ws.audioscrobbler.com/2.0/'

class Proxy(object):
    """Base proxy class"""
    
    def __init__(self, client, name):
        self._client = client
        self._name = name

    def __call__(self, method, args):
        return self._client('%s.%s' % (self._name, method), args)

def _generate_proxies():
    """Generate proxy metaclasses for API namespaces."""
    
    for namespace in API_SCHEMA:
        methods = {}
        for method in API_SCHEMA[namespace]:
            params = ['self']
            body_add_params = []
            for param_name, param_options in API_SCHEMA[namespace][method]:
                param = param_name
                if 'optional' in param_options:
                    param = '%s=None' % param_name
                    body_add_params.append( \
                        'if %s is not None: args["%s"] = %s' %
                        (param_name, param_name, param_name))
                else:
                    body_add_params.append('args["%s"] = %s' %
                                           (param_name, param_name))
                params.append(param)
            body = ['def %s(%s):' % (method, ', '.join(params))]
            body.append('args = {}')
            body += body_add_params
            body.append('return self("%s", args)' % method)
            exec('\n    '.join(body))
            methods[method] = eval(method)
        proxy = type('%sProxy' % namespace.title(), (Proxy, ), methods)
        globals()[proxy.__name__] = proxy

_generate_proxies()


#class ArtistProxy(ArtistProxy):
#    """Example proxy class for artist namespace."""
#    
#    def getInfo(self, artist=None):
#        """An overriden method."""
#        
#        return "custom getInfo"

class LibFM(object):
    """Provides access to last.fm API."""

    def __init__(self, api_key):
        self._api_key = api_key
        
        for namespace in API_SCHEMA:
            self.__dict__[namespace] = eval('%sProxy(self, "%s")' \
                            % (namespace.title(), namespace))

    def __call__(self, name, args=None):
        """Handle standard API methods."""

        url = urllib.urlencode(self._create_post_args(name, args))
        response_string = urllib2.urlopen(LIBFM_URL, url).read()
        return response_string

    def _create_post_args(self, name, args):
        args['method'] = name
        args['api_key'] = self._api_key
        args['format'] = 'json'

        if 'sk' in args:
            args['api_sig'] = self._sign_method(args)
        return args

    def _sign_method(self, args):
        params = args.items()
        params.sort()
        call_mangle = ''
        for name, value in params:
            call_mangle = call_mangle + name + str(value)
        return md5.new(call_mangle).hexdigest()

if __name__ == '__main__':
    # TODO: moves these to a unit test
    libFM = LibFM("b25b959554ed76058ac220b7b2e0a026")
    #print libFM.artist.getInfo()
    #print libFM.user.getRecentTracks('user',page=5)
    print libFM.album.addTags('luna amara','asflat','rock','signature')
