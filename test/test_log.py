#!/usr/bin/python3

# Copyright 2020 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import importlib

import logging
import ops.log


class FakeModelBackend:

    def __init__(self):
        self._calls = []

    def calls(self, clear=False):
        calls = self._calls
        if clear:
            self._calls = []
        return calls

    def juju_log(self, message, level):
        self._calls.append((message, level))


class TestLogging(unittest.TestCase):

    def setUp(self):
        self.backend = FakeModelBackend()

        logging.shutdown()
        importlib.reload(logging)

    def test_default_logging(self):
        ops.log.setup_root_logging(self.backend)

        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.INFO)
        self.assertIsInstance(logger.handlers[0], ops.log.JujuLogHandler)

        test_cases = [(
            lambda: logger.critical('critical'), ('CRITICAL', 'critical')
        ), (
            lambda: logger.error('error'), ('ERROR', 'error')
        ), (
            lambda: logger.warning('warning'), ('WARNING', 'warning')
        ), (
            lambda: logger.info('info'), ('INFO', 'info')
        )]

        for do, res in test_cases:
            do()
            calls = self.backend.calls(clear=True)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0], res)
        else:
            logger.debug('debug')
            calls = self.backend.calls(clear=True)
            self.assertEqual(len(calls), 0)

    def test_handler_filtering(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(ops.log.JujuLogHandler(self.backend, logging.WARNING))
        logger.info('foo')
        self.assertEqual(self.backend.calls(), [])
        logger.warning('bar')
        self.assertEqual(self.backend.calls(), [('WARNING', 'bar')])


if __name__ == '__main__':
    unittest.main()
