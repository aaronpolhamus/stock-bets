"""add dividends table

Revision ID: 8d5db431a533
Revises: 40e1b2b9cb10
Create Date: 2020-09-07 21:24:04.732153

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d5db431a533'
down_revision = '40e1b2b9cb10'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dividends',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol', sa.Text(), nullable=True),
    sa.Column('company', sa.Text(), nullable=True),
    sa.Column('amount', sa.Float(precision=32), nullable=True),
    sa.Column('exec_date', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('balances_and_prices_cache',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('symbol', sa.Text(length=20), nullable=True),
    sa.Column('timestamp', sa.Float(precision=32), nullable=True),
    sa.Column('balance', sa.Float(precision=32), nullable=True),
    sa.Column('price', sa.Float(precision=32), nullable=True),
    sa.Column('value', sa.Float(precision=32), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('game_balances', sa.Column('dividend_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'game_balances', 'dividends', ['dividend_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'game_balances', type_='foreignkey')
    op.drop_column('game_balances', 'dividend_id')
    op.drop_index(op.f('ix_balances_and_prices_cache_timestamp'), table_name='balances_and_prices_cache')
    op.drop_index(op.f('ix_balances_and_prices_cache_symbol'), table_name='balances_and_prices_cache')
    op.drop_index('balances_and_prices_game_user_timestamp_ix', table_name='balances_and_prices_cache')
    op.drop_table('balances_and_prices_cache')
    op.drop_table('dividends')
    # ### end Alembic commands ###
