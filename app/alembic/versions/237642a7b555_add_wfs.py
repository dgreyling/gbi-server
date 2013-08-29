"""add wfs

Revision ID: 237642a7b555
Revises: 392e4f2a9028
Create Date: 2013-08-29 11:54:03.797435

"""

# revision identifiers, used by Alembic.
revision = '237642a7b555'
down_revision = '392e4f2a9028'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(u'wfs',
	    sa.Column(u'id', sa.INTEGER(), primary_key=True, nullable=False),
	    sa.Column(u'name', sa.VARCHAR(), unique=True),
	    sa.Column(u'url', sa.VARCHAR()),
	    sa.Column(u'host', sa.VARCHAR()),

		sa.Column(u'geometry', sa.VARCHAR()),
		sa.Column(u'layer', sa.VARCHAR()),

		sa.Column(u'srs', sa.VARCHAR()),
		sa.Column(u'ns_prefix', sa.VARCHAR()),
		sa.Column(u'ns_uri', sa.VARCHAR()),
	    sa.Column(u'search_property', sa.VARCHAR()),
	    sa.Column(u'max_features', sa.INTEGER()),

	    sa.Column(u'username', sa.VARCHAR()),
	    sa.Column(u'password', sa.VARCHAR()),

	    sa.PrimaryKeyConstraint(u'id')
	)

def downgrade():
    op.drop_table(u'wfs')

