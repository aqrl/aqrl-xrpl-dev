# -*- coding: utf-8 -*-

from .context import aqrl_xrpl
from xrpl.clients import JsonRpcClient

import unittest

class AQRLTestSuite(unittest.TestCase):
    """Test cases."""

    def test_faucet(self):
        self.assertTrue(aqrl_xrpl.create_altnet_faucet())

    def test_account(self):
        wallet = aqrl_xrpl.create_altnet_faucet()
        self.assertTrue(aqrl_xrpl.create_account(wallet))

    def test_xaddress(self):
        wallet = aqrl_xrpl.create_altnet_faucet()
        account = aqrl_xrpl.create_account(wallet)
        self.assertTrue(aqrl_xrpl.create_xaddress(account))

    def lookup_account_info(self):
        pass

if __name__ == '__main__':
    unittest.main()
