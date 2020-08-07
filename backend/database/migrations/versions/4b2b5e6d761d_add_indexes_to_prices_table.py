"""add indexes to prices table

Revision ID: 4b2b5e6d761d
Revises: b50d0c505d3e
Create Date: 2020-08-04 00:15:15.425613

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b2b5e6d761d'
down_revision = 'b50d0c505d3e'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('prices', 'symbol', existing_type=sa.Text, type_=sa.VARCHAR(length=255),
                    existing_nullable=True)

    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_prices_symbol'), 'prices', ['symbol'], unique=False)
    op.create_index(op.f('ix_prices_timestamp'), 'prices', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    op.alter_column('prices', 'symbol', existing_type=sa.VARCHAR(length=255), type_=sa.Text,
                    existing_nullable=True)

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_prices_timestamp'), table_name='prices')
    op.drop_index(op.f('ix_prices_symbol'), table_name='prices')
    # ### end Alembic commands ###