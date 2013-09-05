"""protected option

Revision ID: 59a370260814
Revises: 237642a7b555
Create Date: 2013-09-05 15:58:11.647216

"""

# revision identifiers, used by Alembic.
revision = '59a370260814'
down_revision = '237642a7b555'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('wfs', sa.Column('is_protected', sa.Boolean))
    op.add_column('wmts', sa.Column('is_protected', sa.Boolean))
    op.add_column('wms', sa.Column('is_protected', sa.Boolean))


def downgrade():
    op.drop_column('wfs', 'is_protected')
    op.drop_column('wmts', 'is_protected')
    op.drop_column('wms', 'is_protected')

