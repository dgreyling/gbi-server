"""Added WMS table

Revision ID: 392e4f2a9028
Revises: None
Create Date: 2013-08-16 14:56:41.551716

"""

# revision identifiers, used by Alembic.
revision = '392e4f2a9028'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(u'wms',
    sa.Column(u'id', sa.INTEGER(), primary_key=True, nullable=False),
    sa.Column(u'name', sa.VARCHAR(), unique=True),
    sa.Column(u'url', sa.VARCHAR(), nullable=False),
    sa.Column(u'username', sa.VARCHAR()),
    sa.Column(u'password', sa.VARCHAR()),
    sa.Column(u'title', sa.VARCHAR()),
    sa.Column(u'layer', sa.VARCHAR(), nullable=False),
    sa.Column(u'format', sa.VARCHAR(), nullable=False),
    sa.Column(u'srs', sa.VARCHAR()),
    sa.Column(u'version', sa.VARCHAR()),

    sa.Column(u'view_level_start', sa.VARCHAR()),
    sa.Column(u'view_level_end', sa.VARCHAR()),
    sa.Column(u'is_background_layer', sa.Boolean(), default=False),
    sa.Column(u'is_baselayer', sa.Boolean(), default=False),
    sa.Column(u'is_overlay', sa.Boolean(), default=True),
    sa.Column(u'is_transparent', sa.Boolean(), default=True),
    sa.Column(u'is_visible', sa.Boolean(), default=True),
    sa.Column(u'is_public', sa.Boolean(), default=False),
    sa.Column(u'is_accessible', sa.Boolean(), default=False),

    sa.PrimaryKeyConstraint(u'id')
    )

    op.execute("SELECT AddGeometryColumn('public', 'wms', 'view_coverage', 4326, 'POLYGON', 2);")

def downgrade():
    op.drop_table(u'wms')

