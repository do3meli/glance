# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import testtools
import webob

import glance.api.common
from glance.common import exception


class SimpleIterator(object):
    def __init__(self, file_object, chunk_size):
        self.file_object = file_object
        self.chunk_size = chunk_size

    def __iter__(self):
        def read_chunk():
            return self.fobj.read(self.chunk_size)

        chunk = read_chunk()
        while chunk:
            yield chunk
            chunk = read_chunk()
        else:
            return


class TestSizeCheckedIter(testtools.TestCase):
    def _get_image_metadata(self):
        return {'id': 'e31cb99c-fe89-49fb-9cc5-f5104fffa636'}

    def _get_webob_response(self):
        request = webob.Request.blank('/')
        response = webob.Response()
        response.request = request
        return response

    def test_uniform_chunk_size(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = glance.api.common.size_checked_iter(
            resp, meta, 4, ['AB', 'CD'], None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('CD', next(checked_image))
        self.assertRaises(StopIteration, next, checked_image)

    def test_small_last_chunk(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = glance.api.common.size_checked_iter(
            resp, meta, 3, ['AB', 'C'], None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('C', next(checked_image))
        self.assertRaises(StopIteration, next, checked_image)

    def test_variable_chunk_size(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = glance.api.common.size_checked_iter(
            resp, meta, 6, ['AB', '', 'CDE', 'F'], None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('', next(checked_image))
        self.assertEqual('CDE', next(checked_image))
        self.assertEqual('F', next(checked_image))
        self.assertRaises(StopIteration, next, checked_image)

    def test_too_many_chunks(self):
        """An image should streamed regardless of expected_size"""
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = glance.api.common.size_checked_iter(
            resp, meta, 4, ['AB', 'CD', 'EF'], None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('CD', next(checked_image))
        self.assertEqual('EF', next(checked_image))
        self.assertRaises(exception.GlanceException, next, checked_image)

    def test_too_few_chunks(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = glance.api.common.size_checked_iter(resp, meta, 6,
                                                            ['AB', 'CD'],
                                                            None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('CD', next(checked_image))
        self.assertRaises(exception.GlanceException, next, checked_image)

    def test_too_much_data(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = glance.api.common.size_checked_iter(resp, meta, 3,
                                                            ['AB', 'CD'],
                                                            None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('CD', next(checked_image))
        self.assertRaises(exception.GlanceException, next, checked_image)

    def test_too_little_data(self):
        resp = self._get_webob_response()
        meta = self._get_image_metadata()
        checked_image = glance.api.common.size_checked_iter(resp, meta, 6,
                                                            ['AB', 'CD', 'E'],
                                                            None)

        self.assertEqual('AB', next(checked_image))
        self.assertEqual('CD', next(checked_image))
        self.assertEqual('E', next(checked_image))
        self.assertRaises(exception.GlanceException, next, checked_image)
