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


# The last.fm API schema. Proxy objects are generated based on this.
#
#   The schema contains a dictionary of namespaces.
#   A namespace contains a dictionary of methods.
#   A method contains a list of parameter.
#   A parameter is a tuple containing it's title and a list of flags.
#   The available flags are auto and optional.
#   Parameters flagged as optional may be ommited from method calls.
#   Auto parameters should not be passed with the method call. They are
# provided by the library. This flag is used only by the library.
#   All other parameters are by default required.
#   Parameter order is not important, except that required parameters should be
# placed before all other types of parameters.
#   The api_sig parameter is included by the library automatically, for all
# methods.


API_SCHEMA = {
    'album' : {
            'addTags' : [('artist', []),
                         ('album', []),
                         ('tags', []),
                         ('sk', []),
                         ('api_sig', ['auto']),
                ],
            'getBuylinks' : [('artist', ['optional']),
                             ('album', ['optional']),
                             ('mbid', ['optional']),
                             ('country', ['optional']),
                ],
            'getInfo' : [('artist', ['optional']),
                         ('album', ['optional']),
                         ('mbid', ['optional']),
                         ('username', ['optional']),
                         ('lang', ['optional']),
                ],
            'getTags' : [('artist', []),
                         ('album', []),
                         ('sk', []),
                         ('api_sig', ['auto']),
                ],
            'removeTag' : [('artist', []),
                           ('album', []),
                           ('tag', []),
                           ('sk', []),
                           ('api_sig', ['auto']),
                ],
            'search' : [('album', []),
                        ('limit', ['optional']),
                        ('page', ['optional']),
                ],
            'share' : [('artist', []),
                       ('album', []),
                       ('recipient', []),
                       ('sk', []),
                       ('public', ['optional']),
                       ('message', ['optional']),
                       ('api_sig', ['auto']),
                ],
        },
    'artist' : {
            'addTags' : [('artist', []),
                         ('tags', []),
                         ('sk', []),
                         ('api_sig', ['auto']),
                ],
            'getEvents' : [('artist', []),
                ],
            'getImages' : [('artist', []),
                           ('page', ['optional']),
                           ('limit', ['optional']),
                           ('order', ['optional']),
                ],
            'getInfo' : [('artist', ['optional']),
                         ('mbid', ['optional']),
                         ('username', ['optional']),
                         ('lang', ['optional']),
                ],
            'getPastEvents' : [('artist', []),
                               ('page', ['optional']),
                               ('limit', ['optional']),
                ],
            'getPodcast' : [('artist', []),
                ],
            'getShouts' : [('artist', []),
                           ('limit', []),
                           ('page', []),
                ],
            'getSimilar' : [('artist', []),
                            ('limit', ['optional']),
                ],
            'getTags' : [('artist', []),
                         ('sk', []),
                         ('api_sig', ['auto']),
                ],
            'getTopAlbums' : [('artist', []),
                ],
            'getTopFans' : [('artist', []),
                ],
            'getTopTags' : [('artist', []),
                ],
            'getTopTracks' : [('artist', []),
                ],
            'removeTag' : [('artist', []),
                           ('tag', []),
                           ('sk', []),
                           ('api_sig', ['auto']),
                ],
            'search' : [('artist', []),
                        ('limit', ['optional']),
                        ('page', ['optional']),
                ],
            'share' : [('artist', []),
                       ('recipient', []),
                       ('sk', []),
                       ('message', ['optional']),
                       ('public', ['optional']),
                       ('api_sig', ['auto']),
                ],
            'shout' : [('artist', []),
                       ('message', []),
                       ('sk', []),
                       ('api_sig', ['auto']),
                ],
        },
    'auth' : {
            'getMobileSession' : [('username', []),
                                  ('authToken', []),
                                  ('api_sig', ['auto']),
                ],
            'getSession' : [('token', []),
                            ('api_sig', ['auto'])
                ],
            'getToken' : [('api_sig', ['auto']),
                ],
        },
    'event' : {
            'attend' : [('event', []),
                        ('status', []),
                        ('sk', []),
                        ('api_sig', ['auto']),
                ],
            'getAttendees' : [('event', []),
                ],
            'getInfo' : [('event', []),
                ],
            'getShouts' : [('event', []),
                ],
            'share' : [('event', []),
                       ('recipient', []),
                       ('sk', []),
                       ('public', ['optional']),
                       ('message', ['optional']),
                       ('api_sig', ['auto']),
                ],
            'shout' : [('event', []),
                       ('message', []),
                       ('sk', []),
                       ('api_sig', ['auto']),
                ],
        },
    'geo' : {
            'getEvents' : [('location', ['optional']),
                           ('lat', ['optional']),
                           ('long', ['optional']),
                           ('page', ['optional']),
                           ('distance', ['optional']),
                ],
            'getMetroArtistChart' : [('country', []),
                                     ('metro', []),
                                     ('start', ['optional']),
                                     ('end', ['optional']),
                ],
            'getMetroHypeArtistChart' : [('country', []),
                                         ('metro', []),
                                         ('start', ['optional']),
                                         ('end', ['optional']),
                ],
            'getMetroHypeTrackChart' : [('country', []),
                                        ('metro', []),
                                        ('start', ['optional']),
                                        ('end', ['optional']),
                ],
            'getMetroTrackChart' : [('country', []),
                                    ('metro', []),
                                    ('start', ['optional']),
                                    ('end', ['optional']),
                ],
            'getMetroUniqueArtistChart' : [('country', []),
                                           ('metro', []),
                                           ('start', []),
                                           ('end', []),
                ],
            'getMetroUniqueTrackChart' : [('country', []),
                                          ('metro', []),
                                          ('start', []),
                                          ('end', []),
                ],
            'getMetroWeeklyChartlist' : [
                ],
            'getTopArtists' : [('country', []),
                ],
            'getTopTracks' : [('country', []),
                              ('location', ['optional']),
                ],
        },
    'group' : {
            'getMembers' : [('group', []),
                ],
            'getWeeklyAlbumChart' : [('group', []),
                                     ('from_date', ['optional']),
                                     ('to', ['optional']),
                ],
            'getWeeklyArtistChart' : [('group', []),
                                      ('from_date', ['optional']),
                                      ('to', ['optional']),
                ],
            'getWeeklyChartList' : [('group', []),
                ],
            'getWeeklyTrackChart' : [('group', []),
                                     ('from_date', ['optional']),
                                     ('to', ['optional']),
                ],
        },
    'library' : {
            'addAlbum' : [('artist', []),
                          ('album', []),
                          ('sk', []),
                          ('api_sig', ['auto']),
                ],
            'addArtist' : [('artist', []),
                           ('sk', []),
                           ('api_sig', ['auto']),
                ],
            'addTrack' : [('artist', []),
                          ('track', []),
                          ('sk', []),
                          ('api_sig', ['optional']),
                ],
            'getAlbums' : [('user', []),
                           ('artist', ['optional']),
                           ('limit', ['optional']),
                           ('page', ['optional']),
                ],
            'getArtists' : [('user', []),
                            ('limit', ['optional']),
                            ('page', ['optional']),
                ],
            'getTracks' : [('user', []),
                           ('artist', ['optional']),
                           ('album', ['optional']),
                           ('page', ['optional']),
                           ('limit', ['optional']),
                ],
        },
    'playlist' : {
             'addTrack' : [('playlistID', []),
                           ('track', []),
                           ('artist', []),
                           ('sk', []),
                           ('api_sig', ['auto']),
                ],
             'create' : [('sk', []),
                         ('title', ['optional']),
                         ('description', ['optional']),
                         ('api_sig', ['auto']),
                ],
             'fetch' : [('playlistURL', []),
               ],
        },
    'radio' : {
            'getPlaylist' : [('sk', []),
                             ('discovery', ['optional']),
                             ('rtp', ['optional']),
                             ('bitrate', ['optional']),
                             ('buylinks', ['optional']),
                             ('speed_multiplier', ['optional']),
                             ('api_sig', ['auto']),
               ],
            'tune' : [('station', []),
                      ('sk', []),
                      ('lang', []),
                      ('api_sig', ['auto']),
               ],
        },
    'tag' : {
            'getSimilar' : [('tag', []),
               ],
            'getTopAlbums' : [
               ],
            'getTopArtists' : [
               ],
            'getTopTags' : [
               ],
            'getTopTracks' : [
               ],
            'getWeeklyArtistChart' : [('tag', []),
                                      ('from_date', ['optional']),
                                      ('to', ['optional']),
                                      ('limit', ['optional']), #TODO : needs default value
               ],
            'getWeeklyChartList' : [('tag', []),
               ],
            'search' : [('tag', []),
                        ('limit', ['optional']),
                        ('page', ['optional']),
               ],
        },
    ##############################
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

    def _forward(self, method, args):
        """Forwards the call to the centralized handler"""
        return self._client('%s.%s' % (self._name, method), args)

    def _pack_args(self, *args):
        """
        Packs arguments in a dict, removing those with value None

        Input values are of the form (argname, argvalue, argname, argvalue, ..)
        """
        
        arg_dict = {}
        for arg_name, arg_value in zip(args[0::2], args[1::2]):
            if arg_value is not None:
                arg_dict.update({arg_name : arg_value})
        return arg_dict

    def __call__(self, method, args):
        return self._forward(method, args)

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

class GroupProxy(GroupProxy):
    """Overriding the generated proxy to rename some arguments"""

    def getWeeklyAlbumChart(self, group, from_date=None, to=None):
        args = self._pack_args('group', group, 'from', from_date, 'to', to)
        return self._forward(self.getWeeklyAlbumChart.__name__, args)

    def getWeeklyArtistChart(self, group, from_date=None, to=None):
        args = self._pack_args('group', group, 'from', from_date, 'to', to)
        return self._forward(self.getWeeklyArtistChart.__name__, args)

    def getWeeklyTrackChart(self, group, from_date=None, to=None):
        args = self._pack_args('group', group, 'from', from_date, 'to', to)
        return self._forward(self.getWeeklyTrackChart.__name__, args)

class TagProxy(TagProxy):
    """Overriding the generated proxy to rename some arguments"""

    def getWeeklyArtistChart(self, tag, from_date=None, to=None, limit=None):
        args = self._pack_args('tag', tag, 'from', from_date, 'to', to, \
                               'limit', limit)
        return self._forward(self.getWeeklyArtistChart.__name__, args)

class LibFMError(Exception):

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
            http_response = self._do_request(request_args, request_type)
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

    def _do_request(self, args, request_type):
        if request_type == 'GET':
            call_params = (LIBFM_URL + '?' + args, None)
        else:
            call_params = (LIBFM_URL, args)
        return urllib2.urlopen(call_params[0], call_params[1]).read()

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
