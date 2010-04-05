import md5
import urllib
import urllib2
from xml.dom import minidom
from xml.parsers.expat import ExpatError

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

__all__ = ['LibFM', 'LibFMError', ]


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
            'getTopTracks' : [('artist', []),
                ],
            'getTopFans': [('artist', []),
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
            'getEvents' : [('user', []),
                ],
            'getRecentTracks' : [('user', []),
                                 ('limit', ['optional']),
                                 ('page', ['optional']),
                ],
            'getShouts' : [('user', []),
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
        self.api_key = api_key
        self.secret = secret
        self.force_xml_responses = False
        
        for namespace in API_SCHEMA:
            self.__dict__[namespace] = eval('%sProxy(self, "%s")' \
                            % (namespace.title(), namespace))

    def __call__(self, name, args=None):
        """Handle standard API methods."""

        request_type = 'GET'
        if 'api_sig' in args:
            request_type = 'POST'
        response_format = 'XML'
        if request_type == 'GET' and SIMPLEJSON_LOADED and not \
            self.force_xml_responses:
            response_format = 'JSON'

        request_args = self._create_request_args(name, args, response_format)
        try:
            response = self._do_request(request_args, request_type)
        except urllib2.HTTPError, httpException:
            try:
                # the server will occasionally raise HTTP errors for XML reqs.
                error_body = httpException.read()
                minidom.parseString(error_body)
                return self._parse_xml_response(error_body)
            except ExpatError:
                raise httpException

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
    
    def _node_attributes_to_dict(self, node):
        """
        Create a dictionary from a NamedNodeMap
        
        Required because NamedNodeMap does not behave 100% like a dict
        """
        
        result = {}
        for (key, value) in node.attributes.items():
            result.update({key : value})
        return result

    def _parse_node(self, node):
        if node.nodeType == node.DOCUMENT_NODE:
            return self._parse_node(node.childNodes[0])
        
        if node.nodeType == node.ELEMENT_NODE and \
            len(filter(lambda x : x.nodeType != node.TEXT_NODE, \
                      node.childNodes)) == 0:
            node_text = ''.join(node.data for node in node.childNodes)
            if node.hasAttributes():
                node_content = self._node_attributes_to_dict(node)
                node_content.update({'#text' : node_text})
            else:
                node_content = node_text
            return {node.nodeName : node_content}
            
        if node.nodeType == node.TEXT_NODE:
            return {}
        
        result = {}
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                child_result = self._parse_node(child)
                if len(child_result) == 0:
                    break
                child_name = child_result.keys()[0]
                child_value = child_result.values()[0]
                if child_name in result:
                    if type(result[child_name]) is list:
                        result[child_name].append(child_value)
                    else:
                        result[child_name] = [result[child_name], child_value]
                else:
                    result.update(child_result)
        if node.hasAttributes():
            attributes = self._node_attributes_to_dict(node)
            result.update({'@attr' : attributes})
        return {node.nodeName : result}

    def _parse_xml_response(self, response):
        """Transform XML structure to dictionaries-lists structure"""
        
        xml_doc = minidom.parseString(response)
        result = self._parse_node(xml_doc)
        self._handle_xml_errors(result)
        xml_doc.unlink()
        #strip lfm node & it's attributes
        result = result['lfm']
        del result['@attr']
        return result

    def _parse_json_response(self, response):
        result = simplejson.loads(response)
        self._handle_json_errors(result)
        return result

    def _handle_xml_errors(self, response):
        if 'error' in response['lfm']:
            error = response['lfm']['error']
            raise LibFMError(error['code'], error['#text'])

    def _handle_json_errors(self, response):
        if 'error' in response:
            raise LibFMError(response['error'], response['message'])

    def _create_request_args(self, name, args, response_format):
        """
        Transform method name & args to application/x-www-form-urlencoded

        """
        
        args['method'] = name
        args['api_key'] = self.api_key
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
        return md5.new(call_mangle + self.secret).hexdigest()
