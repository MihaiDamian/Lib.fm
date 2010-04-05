import unittest
from libfm import LibFM
from libfm import LibFMError


class Test(unittest.TestCase):


    def setUp(self):
        self.libFM = LibFM("2b3268cef9e10b81c4359cd03b4e6373", 
                           "f935eb35203409a4fc3f7fc37318ab3e")
        #for generating not-found errors
        self.fake_user = 'erheherhreherhe'
        self.fake_artist = 'wdehgehrhrhrh'


    def test_dynamic_method_loading(self):
        response = self.libFM.artist.getInfo("Nirvana")
        self.assertTrue('artist' in response)
        
    def test_named_parameters(self):
        response = self.libFM.user.getRecentTracks(limit=5, user='rj')
        self.assertTrue('recenttracks' in response)

    def test_response_error_handling(self):
        self.assertRaises(LibFMError, self.libFM.user.getShouts, self.fake_user)
        
    def test_xml_eq_json_normal_response(self):
        xml_response = self.libFM.artist.getTopFans('Pearl Jam')
        self.libFM.force_xml_responses = True
        json_response = self.libFM.artist.getTopFans('Pearl Jam')
        self.assertEqual(xml_response, json_response, 
                         'XML and JSON requests produce different results')
        
    def test_xml_eq_json_error_response(self):
        try:
            xml_response = self.libFM.artist.getTopTracks(self.fake_artist)
            self.fail('Call of artist.getTopTracks with fake artist name %s \
                should have raised an error.' % self.fake_artist)
        except LibFMError, xml_error:
            self.libFM.force_xml_responses = True
            try:
                json_response = self.libFM.artist.getTopTracks(self.fake_artist)
                self.fail('Call of artist.getTopTracks with fake artist name \
                    %s should have raised an error.' % self.fake_artist)
            except LibFMError, json_error:
                self.assertEqual(xml_error, json_error, 'XML and JSON \
                    responses raise different errors')
                

if __name__ == "__main__":
    unittest.main()
