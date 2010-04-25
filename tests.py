import unittest
from libfm import LibFM
from libfm import LibFMError


class TestLibFM(unittest.TestCase):


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
        
    def test_named_parameters(self):
        response = self.libFM.read('user.getRecentTracks', limit=5, user='rj')
        self.assertTrue('recenttracks' in response,
                        'Named parameters should work on generated methods')

    def test_no_parameters(self):
        """Making sure methods w/o parameters work fine"""
        response = self.libFM.read('geo.getMetroWeeklyChartlist')
        self.assertTrue('weeklychartlist' in response, 'Error in method w/o \
                parameters')

    def test_response_error_handling(self):
        """Checking exceptions raised from error codes"""
        self.assertRaises(LibFMError, self.libFM.read, 'user.getShouts',
                                                      user=self.fake_user)

    @session
    def test_write_method(self):
        print 'here'
        response = self.libFM.write('artist.addTags', artist='Pearl Jam',
                                    tags='Grunge', sk=self.session_key)
        if 'status' in response:
            if response['status'] == 'ok':
                return
        self.assertTrue(False, 'Method failed to write')
        
    def test_xml_eq_json_normal_response(self):
        """Check if XML and JSON responses are seamless"""
        xml_response = self.libFM.read('artist.getTopFans', artist='Pearl Jam')
        self.libFM.force_xml_responses = True
        json_response = self.libFM.read('artist.getTopFans',
                                        artist='Pearl Jam')
        self.assertEqual(xml_response, json_response, 
                         'XML and JSON requests produce different results')
        
    def test_xml_eq_json_error_response(self):
        """Check if error containing XML and JSON responses are seamless"""
        try:
            self.libFM.read('artist.getTopTracks', artist=self.fake_artist)
            self.fail('Call of artist.getTopTracks with fake artist name %s \
                should have raised an error.' % self.fake_artist)
        except LibFMError, xml_error:
            self.libFM.force_xml_responses = True
            try:
                self.libFM.read('artist.getTopTracks', artist=self.fake_artist)
                self.fail('Call of artist.getTopTracks with fake artist name \
                    %s should have raised an error.' % self.fake_artist)
            except LibFMError, json_error:
                self.assertEqual(xml_error, json_error, 
                            'XML and JSON responses raise different errors')
    
                
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
