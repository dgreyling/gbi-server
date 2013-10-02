"""Removed columns matrix_set, layer and srs from WMTS

Revision ID: 35ef3dcd2cd2
Revises: 59a370260814
Create Date: 2013-10-01 14:34:14.659592

"""

# revision identifiers, used by Alembic.
revision = '35ef3dcd2cd2'
down_revision = '59a370260814'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('wmts', 'matrix_set')
    op.drop_column('wmts', 'srs')
    op.drop_column('wmts', 'layer')

def downgrade():
    op.add_column('wmts', sa.Column('matrix_set', sa.String(64), default='GoogleMapsCompatible'))
    op.add_column('wmts', sa.Column('srs', sa.String(64), default="EPSG:3857"))
    op.add_column('wmts', sa.Column('layer', sa.String(256)))
