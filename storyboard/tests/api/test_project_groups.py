# Copyright (c) 2014 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
from urllib import urlencode

from webtest.app import AppError

from storyboard.db.models import ProjectGroup
from storyboard.db.models import User
from storyboard.tests import base


class TestProjectGroups(base.FunctionalTest):

    def setUp(self):
        super(TestProjectGroups, self).setUp()

        self.resource = '/project_groups'

        self.group_01 = {
            'name': 'test-group',
            'title': 'with a title'
        }

        self.load_data([
            User(id=1,
                 username='superuser',
                 email='superuser@example.com',
                 full_name='Super User',
                 is_superuser=True),
            ProjectGroup(
                id=1,
                name='group-one',
                title='Project Group Title'
            )
        ])
        su_token = self.build_access_token(1)
        self.default_headers['Authorization'] = 'Bearer %s' % (
            su_token.access_token)

    def test_projects_endpoint(self):
        response = self.get_json(path=self.resource)
        self.assertEqual(1, len(response))

    def test_get(self):
        response = self.get_json(path=self.resource + "/1")
        self.assertEqual(1, response['id'])
        self.assertEqual("group-one", response['name'])
        self.assertEqual("Project Group Title", response['title'])

    def test_get_empty(self):
        response = self.get_json(path=self.resource + "/999",
                                 expect_errors=True)
        self.assertEqual(404, response.status_code)

    def test_create(self):
        response = self.post_json(self.resource, self.group_01)
        project_group = json.loads(response.body)

        self.assertEqual(self.group_01['name'], project_group['name'])
        self.assertEqual(self.group_01['title'], project_group['title'])

    def test_create_invalid(self):

        invalid_project_group = self.group_01.copy()
        invalid_project_group["name"] = "name with spaces"

        self.assertRaises(AppError, self.post_json, self.resource,
                          invalid_project_group)

    def test_update(self):
        response = self.post_json(self.resource, self.group_01)
        original = json.loads(response.body)

        delta = {
            'id': original['id'],
            'name': 'new-name',
            'title': 'new title'
        }

        url = "/project_groups/%d" % original['id']
        response = self.put_json(url, delta)
        updated = json.loads(response.body)

        self.assertEqual(original['id'], updated['id'])

        self.assertNotEqual(original['name'], updated['name'])
        self.assertNotEqual(original['title'], updated['title'])

    def test_update_invalid(self):
        response = self.post_json(self.resource, self.group_01)
        original = json.loads(response.body)

        delta = {
            'id': original['id'],
            'name': 'new-name is invalid!',
        }

        url = "/project_groups/%d" % original['id']

        # check for invalid characters like space and '!'
        self.assertRaises(AppError, self.put_json, url, delta)

        delta["name"] = "a"

        # check for a too short name
        self.assertRaises(AppError, self.put_json, url, delta)


class TestProjectGroupSearch(base.FunctionalTest):
    def setUp(self):
        super(TestProjectGroupSearch, self).setUp()

        self.resource = '/project_groups'

        self.load_data([
            ProjectGroup(
                id=1,
                name='projectgroup1',
                title='C Sort - foo'
            ),
            ProjectGroup(
                id=2,
                name='projectgroup2',
                title='B Sort - bar'
            ),
            ProjectGroup(
                id=3,
                name='projectgroup3',
                title='A Sort - foo'
            )
        ])

    def build_search_url(self, params):
        return '/project_groups?%s' % (urlencode(params))

    def test_search_by_name(self):
        url = self.build_search_url({
            'name': 'projectgroup2'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(1, len(results.json))
        self.assertEqual('1', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual('projectgroup2', result['name'])

    def test_search_by_title(self):
        url = self.build_search_url({
            'title': 'foo'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(2, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])
        result = results.json[1]
        self.assertEqual(3, result['id'])

    def test_search_limit(self):
        url = self.build_search_url({
            'title': 'foo',
            'limit': 1
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(1, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertEqual('1', results.headers['X-Limit'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])

    def test_search_marker(self):
        url = self.build_search_url({
            'title': 'foo',
            'marker': 1  # Last item in previous list.
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(1, len(results.json))
        self.assertEqual('2', results.headers['X-Total'])
        self.assertEqual('1', results.headers['X-Marker'])

        result = results.json[0]
        self.assertEqual(3, result['id'])

    def test_search_direction(self):
        url = self.build_search_url({
            'sort_field': 'title',
            'sort_dir': 'asc'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(3, len(results.json))
        self.assertEqual('3', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(3, result['id'])
        result = results.json[1]
        self.assertEqual(2, result['id'])
        result = results.json[2]
        self.assertEqual(1, result['id'])

    def test_search_direction_desc(self):
        url = self.build_search_url({
            'sort_field': 'title',
            'sort_dir': 'desc'
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(3, len(results.json))
        self.assertEqual('3', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)

        result = results.json[0]
        self.assertEqual(1, result['id'])
        result = results.json[1]
        self.assertEqual(2, result['id'])
        result = results.json[2]
        self.assertEqual(3, result['id'])

    def test_search_no_results(self):
        url = self.build_search_url({
            'title': 'zing',
        })

        results = self.get_json(url, expect_errors=True)
        self.assertEqual(0, len(results.json))
        self.assertEqual('0', results.headers['X-Total'])
        self.assertFalse('X-Marker' in results.headers)
