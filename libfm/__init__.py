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


LIBFM_URL = 'http://ws.audioscrobbler.com/2.0/'

class LibFMError(Exception):

    invalid_secret_key = 100

    def __init__(self, code, message):
        self.code = int(code)
        self.message = message

    def __str__(self):
        return 'Error %s: %s' % (self.code, self.message)
    
    def __eq__(self, other):
        if isinstance(other, LibFMError):
            return self.code == other.code and self.message == other.message
        else:
            return NotImplemented

class LibFM(object):
    """Provides access to last.fm API."""

    def __init__(self, api_key, secret=None):
        self.api_key = api_key
        self.secret = secret
        self.session_key = None
        self.force_xml_responses = False
        self.proxy = None

    def read(self, method, **kwargs):
        return self._call_method(method, kwargs, 'r')

    def write(self, method, **kwargs):
        return self._call_method(method, kwargs, 'w')

    def get_token(self):
        return self._call_method('auth.getToken', mode='w')

    def create_session(self, token):
        response = self._call_method('auth.getSession', {'token' : token},
                                 mode='w')
        self.session_key = response['session']['key']
        return response

    def create_mobile_session(self, username, password):
        auth_token = self._create_auth_token(username, password)
        response = self._call_method('auth.getMobileSession',
                        {'username' : username, 'authToken' : auth_token,},
                        'w')
        self.session_key = response['session']['key']
        return response

    def _call_method(self, name, args={}, mode='r'):
        """Handle standard API methods."""
        
        request_type = 'GET'
        if mode is 'w':
            request_type = 'POST'
        
        response_format = 'XML'
        if request_type == 'GET' and SIMPLEJSON_LOADED and not \
            self.force_xml_responses:
            response_format = 'JSON'

        request_args = self._create_request_args(name, args, response_format,
                                                 mode)
        try:
            http_response = self._send_request(request_type, request_args)
        except urllib2.HTTPError, httpException:
            try:
                # the server will occasionally raise HTTP errors for XML reqs.
                error_body = httpException.read()
                minidom.parseString(error_body)
                response = XMLResponse(error_body)
                return response.parse()
            except ExpatError:
                raise httpException
            
        if response_format == 'JSON':
            response = JSONResponse(http_response)
        else:
            response = XMLResponse(http_response)
            
        return response.parse()

    def _send_request(self, request_type, request_args):
        if request_type == 'GET':
            call_params = (LIBFM_URL + '?' + request_args, None)
        else:
            call_params = (LIBFM_URL, request_args)
        if self.proxy is not None:
            proxy_handler = urllib2.ProxyHandler({'http' : self.proxy})
            opener = urllib2.build_opener(proxy_handler)
            return opener.open(call_params[0], call_params[1]).read()
        else:
            return urllib2.urlopen(call_params[0], call_params[1]).read()

    def _create_request_args(self, name, args, response_format, mode):
        """
        Transform method name & args to application/x-www-form-urlencoded

        """
        
        args['method'] = name
        args['api_key'] = self.api_key
        if response_format == 'JSON':
            args['format'] = 'json'

        if mode is 'w':
            args['sk'] = self.session_key
            args['api_sig'] = self._sign_method(args)
        
        return urllib.urlencode(args)

    def _sign_method(self, args):
        if self.secret is None:
            raise LibFMError(LibFMError.invalid_secret_key,
                             'You need to provide a valid secret key.')
        
        params = args.items()
        params.sort()
        call_mangle = ''
        for name, value in params:
            call_mangle = call_mangle + name + str(value)
        return md5.new(call_mangle + self.secret).hexdigest()

    def _create_auth_token(self, username, password):
        username = username.lower()
        password_hash = md5.new(password).hexdigest()
        return md5.new(username + password_hash).hexdigest()
        
    
class LibFMResponse(object):
    """Base class for handling lib.fm responses."""
    
    def __init__(self, response):
        """Takes as input the string content of a HTTP response"""
        self.response = response
        
    def parse(self):
        """
        Each subclass should implement this.
        
        Returns a JSON-like dictionary-list structure.
        """
        pass
    
class JSONResponse(LibFMResponse):
    
    def parse(self):
        result = simplejson.loads(self.response)
        self._handle_errors(result)
        return result
    
    def _handle_errors(self, response):
        if 'error' in response:
            raise LibFMError(response['error'], response['message'])

class XMLResponse(LibFMResponse):
    
    def parse(self):
        """Transform XML structure to dictionaries-lists structure"""
        
        xml_doc = minidom.parseString(self.response)
        if xml_doc.nodeType == xml_doc.DOCUMENT_NODE:
            xml_doc = xml_doc.childNodes[0]
        result = self._parse_node(xml_doc)
        self._handle_errors(result)
        xml_doc.unlink()
        #strip lfm node & it's attributes
        result = result['lfm']
        if '@attr' in result:
            del result['@attr']
        return result
    
    def _handle_errors(self, response):
        if 'error' in response['lfm']:
            error = response['lfm']['error']
            raise LibFMError(error['code'], error['#text'])
    
    def _parse_node(self, node):
        #parse nodes that contain only text or CDATA
        if node.nodeType == node.ELEMENT_NODE and \
            len(filter(lambda x : x.nodeType != node.TEXT_NODE and \
                x.nodeType != node.CDATA_SECTION_NODE, node.childNodes)) == 0:
            node_text = ''.join(node.data for node in node.childNodes)
            if node.hasAttributes():
                node_content = self._parse_node_attributes(node)
                node_content.update({'#text' : node_text})
            else:
                node_content = node_text
            return {node.nodeName : node_content}
        
        #recursively parse nodes that contain other nodes
        result = self._parse_child_elements(node)
        if node.hasAttributes():
            attributes = self._parse_node_attributes(node)
            if len(attributes) > 0:
                result.update({'@attr' : attributes})
        return {node.nodeName : result}
    
    def _parse_child_elements(self, node):
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
        return result
    
    def _parse_node_attributes(self, node):
        """
        Create a dictionary from a NamedNodeMap and discards namespace nodes
        
        NamedNodeMap does not behave 100% like a dict.
        Namespaces are ignored since they're not available in JSON
        """
        
        result = {}
        for (key, value) in node.attributes.items():
            if ':' not in key:
                result.update({key : value})
        return result
