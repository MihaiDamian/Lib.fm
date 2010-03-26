'''
Created on Mar 22, 2010

@author: Mihai
'''
import unittest
from libfm import LibFM
from libfm import LibFMError


class Test(unittest.TestCase):


    def setUp(self):
        self.libFM = LibFM("2b3268cef9e10b81c4359cd03b4e6373", "f935eb35203409a4fc3f7fc37318ab3e")


    def test_dynamic_method_loading(self):
        response = self.libFM.artist.getInfo("Nirvana")
        self.assertTrue('artist' in response)
        
    def test_named_parameters(self):
        response = self.libFM.user.getRecentTracks(limit=5, user='rj')
        self.assertTrue('recenttracks' in response)

    def test_response_error_handling(self):
        self.assertRaises(LibFMError, self.libFM.user.getShouts, 'erheherhreherhe')


if __name__ == "__main__":
    unittest.main()
