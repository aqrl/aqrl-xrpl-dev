# -*- coding: utf-8 -*-

from .context import aqrl-xrpl

import unittest

class AQRLTestSuite(unittest.TestCase):
    """Test cases."""

    def test_faucet(self):
        self.assertTrue(aqrl-xrpl.create_faucet())


if __name__ == '__main__':
    unittest.main()
