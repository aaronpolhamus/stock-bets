"""add return and game count to ratings

Revision ID: 131550301ed3
Revises: 1d3fc8274ad8
Create Date: 2020-10-05 16:34:31.801234

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '131550301ed3'
down_revision = '1d3fc8274ad8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('external_invites', 'status',
               existing_type=mysql.ENUM('invited', 'accepted', 'error', 'declined'),
               nullable=True)
    op.add_column('stockbets_rating', sa.Column('basis', sa.Float(precision=32), nullable=True))
    op.add_column('stockbets_rating', sa.Column('n_games', sa.Integer(), nullable=True))
    op.add_column('stockbets_rating', sa.Column('total_return', sa.Float(precision=32), nullable=True))
    op.drop_index('ix_stockbets_rating_index_symbol', table_name='stockbets_rating')
    op.create_foreign_key(None, 'stockbets_rating', 'index_metadata', ['index_symbol'], ['symbol'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'stockbets_rating', type_='foreignkey')
    op.create_index('ix_stockbets_rating_index_symbol', 'stockbets_rating', ['index_symbol'], unique=False)
    op.drop_column('stockbets_rating', 'total_return')
    op.drop_column('stockbets_rating', 'n_games')
    op.drop_column('stockbets_rating', 'basis')
    op.alter_column('external_invites', 'status',
               existing_type=mysql.ENUM('invited', 'accepted', 'error', 'declined'),
               nullable=False)
    # ### end Alembic commands ###
