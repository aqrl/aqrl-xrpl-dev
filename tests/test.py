# -*- coding: utf-8 -*-

from .context import aqrl_xrpl
from xrpl.clients import JsonRpcClient

import unittest

JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"

def get_test_client():
    return JsonRpcClient(JSON_RPC_URL)

class AQRLTestSuite(unittest.TestCase):
    """Test cases."""

    def test_faucet(self):
        client = get_test_client()
        self.assertTrue(aqrl_xrpl.create_faucet(client))


if __name__ == '__main__':
    unittest.main()
