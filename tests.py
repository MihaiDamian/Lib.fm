import inspect
import unittest
from libfm import LibFM
from libfm import LibFMError


class TestLibFM(unittest.TestCase):

    TESTS = (
        (lambda target : target.artist.getInfo('Down'), None),
        #(lambda target : target.artist.getEvents('Kiss'), None),
    )


    def setUp(self):
        self.libFM = LibFM('2b3268cef9e10b81c4359cd03b4e6373', 
                           'f935eb35203409a4fc3f7fc37318ab3e')
        #for generating not-found errors
        self.fake_user = 'erheherhreherhe'
        self.fake_artist = 'wdehgehrhrhrh'
        #see http://www.last.fm/api/desktopauth for how to generate your own sk
        self.session_key = None

    def session(method):
        """Skip methods that require authentication when sk is not hardcoded"""
        
        def wrapper(self, *args, **kwargs):
            if self.session_key != None:
                return method(self, *args, **kwargs)
            else:
                return
        return wrapper

    def test_dynamic_method_loading(self):
        """Sanity check on dynamically generated API methods"""
        response = self.libFM.artist.getInfo('Nirvana')
        self.assertTrue('artist' in response)
        
    def test_named_parameters(self):
        response = self.libFM.user.getRecentTracks(limit=5, user='rj')
        self.assertTrue('recenttracks' in response,
                        'Named parameters should work on generated methods')

    def test_response_error_handling(self):
        """Checking exceptions raised from error codes"""
        self.assertRaises(LibFMError, self.libFM.user.getShouts, self.fake_user)

    @session
    def test_write_method(self):
        response = self.libFM.artist.addTags('Pearl Jam', 'Grunge',
                                            self.session_key)
        if 'status' in response:
            if response['status'] == 'ok':
                return
        self.assertTrue(False, 'Method failed to write')
        
    def test_xml_eq_json_normal_response(self):
        """Check if XML and JSON responses are seamless"""
        xml_response = self.libFM.artist.getTopFans('Pearl Jam')
        self.libFM.force_xml_responses = True
        json_response = self.libFM.artist.getTopFans('Pearl Jam')
        self.assertEqual(xml_response, json_response, 
                         'XML and JSON requests produce different results')
        
    def test_xml_eq_json_error_response(self):
        """Check if error containing XML and JSON responses are seamless"""
        try:
            self.libFM.artist.getTopTracks(self.fake_artist)
            self.fail('Call of artist.getTopTracks with fake artist name %s \
                should have raised an error.' % self.fake_artist)
        except LibFMError, xml_error:
            self.libFM.force_xml_responses = True
            try:
                self.libFM.artist.getTopTracks(self.fake_artist)
                self.fail('Call of artist.getTopTracks with fake artist name \
                    %s should have raised an error.' % self.fake_artist)
            except LibFMError, json_error:
                self.assertEqual(xml_error, json_error, 
                            'XML and JSON responses raise different errors')
                
    class DifferentResultsError(Exception):

        def __init__(self, message, result1, result2):
            self.message = message
            self.result1 = result1
            self.result2 = result2

        def __str__(self):
            return '%s\n%s\n%s' % (self.message, self.result1, self.result2)

    @session
    def test_all_methods(self):
        """Invoking all API methods"""
        test_status = True
        for test_function, expected_result in TestLibFM.TESTS:
            try:
                self.libFM.force_xml_responses = False
                json = test_function(self.libFM)
                self.libFM.force_xml_responses = True
                xml = test_function(self.libFM)
                if json != xml:
                    raise TestLibFM.DifferentResultsError(
                        'XML and JSON responses differ', xml, json)
                if expected_result is not None:
                    if json != expected_result:
                        raise TestLibFM.DifferentResultsError(
                                'Wrong result', json, expected_result)
                    if xml != expected_result:
                        raise TestLibFM.DifferentResultsError(
                                'Wrong result', xml, expected_result)
            except Exception, ex:
                print ex
                print 'Error encountered in API call: %s' % \
                            inspect.getsource(test_function)
                test_status = False
        self.assertTrue(test_status, 'Some API calls have failed')
    
                
class TestLibFMError(unittest.TestCase):
    
    def test_libfmerror(self):
        err0 = LibFMError('1', 'Error message')
        err1 = LibFMError('1', 'Error message')
        err2 = LibFMError(1, 'Error message')
        err3 = LibFMError('2', 'Error message')
        err4 = LibFMError('1', 'Message')
        self.assertTrue(err0 == err1, 'Identical errors should be equal')
        self.assertTrue(err0 == err2, 
                    'Error codes specified as str or int should be equal')
        self.assertFalse(err0 == err3, 
                    'Errors with different error codes should be different')
        self.assertFalse(err0 == err4, 
                    'Errors with different messages should be different')
                

if __name__ == "__main__":
    unittest.main()
