# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

"""is-automation-user

Revision ID: 058
Revises: 057
Create Date: 2016-05-24 21:51:59.451550

"""

# revision identifiers, used by Alembic.
revision = '058'
down_revision = '057'


from alembic import op
import sqlalchemy as sa


def upgrade(active_plugins=None, options=None):

    op.add_column(
        'users',
        sa.Column('is_automation_user', sa.Boolean(),
        default=False,
        nullable=False))


def downgrade(active_plugins=None, options=None):

    op.drop_column('tasks', 'link')
