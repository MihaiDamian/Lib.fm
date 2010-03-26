import md5
import urllib
import urllib2
from xml.dom import minidom

SIMPLEJSON_LOADED = True
try:
    import json as simplejson
except ImportError:
    try:
        import simplejson
    except ImportError:
        try:
            from django.utils import simplejson
        except ImportError:
            SIMPLEJSON_LOADED = False

__all__ = ['LibFM']


# The last.fm API schema. Proxy objects are generated based on this
API_SCHEMA = {
    'album' : {
            'addTags' : [('artist', []),
                         ('album', []),
                         ('tags', []),
                         ('sk', []),
                         ('api_sig', ['auto']),
                ],
        },
    'artist' : {
            'addTags' : [('artist', []),
                         ('tags', []),
                         ('sk', []),
                         ('api_sig', ['auto']),
                ],
            'getInfo' : [('artist', ['optional']),
                         ('mbid', ['optional']),
                         ('username', ['optional']),
                         ('lang', ['optional']),
                ],
            'getEvents' : [('artist', []),
                ],
        },
    'auth' : {
            'getToken' : [('api_sig', ['auto']),
                ],
            'getSession' : [('token', []),
                            ('api_sig', ['auto'])
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
                if 'optional' in param_options or 'auto' in param_options:
                    param = '%s=None' % param_name
                if 'optional' in param_options:
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

class LibFMError(Exception):

    def __init__(self, code, message):
        self._code = code
        self._message = message

    def __str__(self):
        return 'Error %s: %s' % (self._code, self._message)

class LibFM(object):
    """Provides access to last.fm API."""

    def __init__(self, api_key, secret):
        self._api_key = api_key
        self._secret = secret
        
        for namespace in API_SCHEMA:
            self.__dict__[namespace] = eval('%sProxy(self, "%s")' \
                            % (namespace.title(), namespace))

    def __call__(self, name, args=None):
        """Handle standard API methods."""

        request_type = 'GET'
        if 'api_sig' in args:
            request_type = 'POST'
        response_format = 'XML'
        if request_type == 'GET' and SIMPLEJSON_LOADED:
            response_format = 'JSON'

        request_args = self._create_request_args(name, args, response_format)
        response = self._do_request(request_args, request_type)

        if response_format == 'JSON':
            return self._parse_json_response(response)
        else:
            return self._parse_xml_response(response)

    def _do_request(self, args, request_type):
        if request_type == 'GET':
            call_params = (LIBFM_URL + '?' + args, None)
        else:
            call_params = (LIBFM_URL, args)
        return urllib2.urlopen(call_params[0], call_params[1]).read()

    def _parse_xml_response(self, reponse):
        return reponse

    def _parse_json_response(self, response):
        result = simplejson.loads(response)
        self._handle_errors(result)
        return result

    def _handle_errors(self, response):
        if 'error' in response:
            raise LibFMError(response['error'], response['message'])

    def _create_request_args(self, name, args, response_format):
        """
        Transform method name & args to application/x-www-form-urlencoded

        """
        
        args['method'] = name
        args['api_key'] = self._api_key
        if response_format == 'JSON':
            args['format'] = 'json'

        if 'api_sig' in args:
            del args['api_sig']
            args['api_sig'] = self._sign_method(args)
        return urllib.urlencode(args)

    def _sign_method(self, args):
        params = args.items()
        params.sort()
        call_mangle = ''
        for name, value in params:
            call_mangle = call_mangle + name + str(value)
        return md5.new(call_mangle + self._secret).hexdigest()
