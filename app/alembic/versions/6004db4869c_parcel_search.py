"""Parcel search

Revision ID: 6004db4869c
Revises: 2e222317d9ce
Create Date: 2016-01-21 11:13:44.508580

"""

# revision identifiers, used by Alembic.
revision = '6004db4869c'
down_revision = '2e222317d9ce'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import geoalchemy2


def upgrade():
    op.create_table(
        'search_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('time', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'search_log_geometries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('search_log_id', sa.Integer(), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(
            geometry_type='POLYGON', srid=3857), nullable=True),
        sa.Column('identifier', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['search_log_id'], ['search_logs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('search_log_geometries')
    op.drop_table('search_logs')
