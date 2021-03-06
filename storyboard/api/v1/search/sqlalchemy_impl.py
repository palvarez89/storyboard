# Copyright (c) 2014 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from sqlalchemy import and_, or_
from sqlalchemy.orm import subqueryload
from sqlalchemy.sql.expression import false, true
from sqlalchemy_fulltext import FullTextSearch
import sqlalchemy_fulltext.modes as FullTextMode

from storyboard.api.v1.search import search_engine
from storyboard.db.api import base as api_base
from storyboard.db import models


class SqlAlchemySearchImpl(search_engine.SearchEngine):
    def _build_fulltext_search(self, model_cls, query, q):
        query = query.filter(FullTextSearch(q, model_cls,
                                            mode=FullTextMode.BOOLEAN))

        return query

    def _apply_pagination(self, model_cls, query, marker=None,
                          offset=None, limit=None):

        marker_entity = None
        if marker:
            marker_entity = api_base.entity_get(model_cls, marker, True)

        return api_base.paginate_query(query=query,
                                       model=model_cls,
                                       limit=limit,
                                       sort_key="id",
                                       marker=marker_entity,
                                       offset=offset)

    def projects_query(self, q, sort_dir=None, marker=None,
                       offset=None, limit=None):
        session = api_base.get_session()
        query = api_base.model_query(models.Project, session)
        query = self._build_fulltext_search(models.Project, query, q)
        query = self._apply_pagination(
            models.Project, query, marker, offset, limit)

        return query.all()

    def stories_query(self, q, marker=None, offset=None,
                      limit=None, current_user=None, **kwargs):
        session = api_base.get_session()

        subquery = api_base.model_query(models.Story, session)

        # Filter out stories that the current user can't see
        subquery = subquery.outerjoin(models.story_permissions,
                                      models.Permission,
                                      models.user_permissions,
                                      models.User)
        if current_user is not None:
            subquery = subquery.filter(
                or_(
                    and_(
                        models.User.id == current_user,
                        models.Story.private == true()
                    ),
                    models.Story.private == false()
                )
            )
        else:
            subquery = subquery.filter(models.Story.private == false())

        subquery = self._build_fulltext_search(models.Story, subquery, q)
        subquery = self._apply_pagination(models.Story,
                                          subquery, marker, offset, limit)

        subquery = subquery.subquery('stories_with_idx')

        query = api_base.model_query(models.StorySummary)\
            .options(subqueryload(models.StorySummary.tags))
        query = query.join(subquery,
                           models.StorySummary.id == subquery.c.id)

        stories = query.all()
        return stories

    def tasks_query(self, q, marker=None, offset=None, limit=None,
                    current_user=None, **kwargs):
        session = api_base.get_session()
        query = api_base.model_query(models.Task, session)

        # Filter out tasks or stories that the current user can't see
        query = query.outerjoin(models.Story,
                                models.story_permissions,
                                models.Permission,
                                models.user_permissions,
                                models.User)
        if current_user is not None:
            query = query.filter(
                or_(
                    and_(
                        models.User.id == current_user,
                        models.Story.private == true()
                    ),
                    models.Story.private == false()
                )
            )
        else:
            query = query.filter(models.Story.private == false())

        query = self._build_fulltext_search(models.Task, query, q)
        query = self._apply_pagination(
            models.Task, query, marker, offset, limit)

        return query.all()

    def comments_query(self, q, marker=None, offset=None,
                       limit=None, **kwargs):
        session = api_base.get_session()
        query = api_base.model_query(models.Comment, session)
        query = self._build_fulltext_search(models.Comment, query, q)
        query = self._apply_pagination(
            models.Comment, query, marker, offset, limit)

        return query.all()

    def users_query(self, q, marker=None, offset=None, limit=None, **kwargs):
        session = api_base.get_session()
        query = api_base.model_query(models.User, session)
        query = self._build_fulltext_search(models.User, query, q)
        query = self._apply_pagination(
            models.User, query, marker, offset, limit)

        return query.all()
