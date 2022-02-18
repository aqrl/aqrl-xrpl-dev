# -*- coding: utf-8 -*-

from .context import aqrl_xrpl
from xrpl.clients import JsonRpcClient

import unittest

class AQRLTestSuite(unittest.TestCase):
    """Test cases."""

    def test_faucet(self):
        self.assertTrue(aqrl_xrpl.create_altnet_faucet())

if __name__ == '__main__':
    unittest.main()
