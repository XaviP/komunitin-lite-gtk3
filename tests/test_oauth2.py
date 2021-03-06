import unittest
from unittest.mock import Mock, patch
import configparser
import time
import json
import os

from komunitin_lite.core.oauth2 import ApiAccess
from tests.fake_objects import CONFIG_SERVER


class TestOauth2(unittest.TestCase):
    def setUp(self):
        self.test_config = configparser.ConfigParser()
        self.test_config['server'] = CONFIG_SERVER
        di = os.path.dirname(__file__)
        with open(os.path.join(di, 'json/oauth2_response.json'), 'r') as f:
            self.server_oauth2_response = json.load(f)
        self.local_data = {
            'user': 'user@test.server.com',
            'auth': self.server_oauth2_response
        }
        self.local_data["auth"]["created"] = int(time.time())

    @patch('komunitin_lite.core.oauth2.get_local_data')
    def test_init_no_data(self, mock_get_data):
        mock_get_data.return_value = {}
        access = ApiAccess(self.test_config)
        access.get_local_auth()
        self.assertTrue(access.user == "")
        self.assertTrue(access._auth == {})
        self.assertTrue(access.has_access is False)

    @patch('komunitin_lite.core.oauth2.requests.post')
    @patch('komunitin_lite.core.oauth2.put_local_data')
    @patch('komunitin_lite.core.oauth2.get_local_data')
    def test_init_with_data(self, mock_get_data, mock_put_data, mock_post):
        # token expired
        self.local_data["auth"]["created"] = 0
        mock_get_data.return_value = self.local_data
        access1 = ApiAccess(self.test_config)
        access1.get_local_auth()
        self.assertTrue(access1.user == "user@test.server.com")
        self.assertTrue(access1._auth == {})
        self.assertTrue(access1.has_access is False)

        # valid token, try to refresh
        self.local_data["auth"]["created"] = int(time.time())
        mock_get_data.return_value = self.local_data
        mock_put_data.return_value = True
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.return_value = self.server_oauth2_response
        mock_post.return_value = response_mock
        access2 = ApiAccess(self.test_config)
        access2.get_local_auth()
        self.assertTrue(access2.user == "user@test.server.com")
        self.assertTrue(access2._auth["access_token"] ==
                        self.server_oauth2_response["access_token"])
        self.assertTrue(access2.has_access is True)

    @patch('komunitin_lite.core.oauth2.requests.post')
    @patch('komunitin_lite.core.oauth2.put_local_data')
    @patch('komunitin_lite.core.oauth2.get_local_data')
    def test_new_access(self, mock_get_data, mock_put_data, mock_post):
        # No data
        mock_get_data.return_value = {}
        access3 = ApiAccess(self.test_config)
        access3.get_local_auth()
        self.assertTrue(access3.has_access is False)

        # Try to authenticate
        mock_put_data.return_value = True
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.return_value = self.server_oauth2_response
        mock_post.return_value = response_mock
        access3.new_access("user@test.server.com", "tests_password")

        # Check data in access3
        self.assertTrue(access3.user == "user@test.server.com")
        self.assertTrue(access3._auth["access_token"] ==
                        self.server_oauth2_response["access_token"])
        self.assertTrue(access3.has_access is True)


if __name__ == '__main__':
    unittest.main()
