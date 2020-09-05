"""remove balances and prices cache

Revision ID: 40e1b2b9cb10
Revises: 5af4e7cabc0e
Create Date: 2020-08-31 02:42:39.495418

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '40e1b2b9cb10'
down_revision = '5af4e7cabc0e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TABLE balances_and_prices_cache DROP FOREIGN KEY balances_and_prices_cache_ibfk_1")
    op.execute("ALTER TABLE balances_and_prices_cache DROP FOREIGN KEY balances_and_prices_cache_ibfk_2")
    op.drop_index('balances_and_prices_game_user_timestamp_ix', table_name='balances_and_prices_cache')
    op.drop_index('ix_balances_and_prices_cache_symbol', table_name='balances_and_prices_cache')
    op.drop_index('ix_balances_and_prices_cache_timestamp', table_name='balances_and_prices_cache')
    op.drop_table('balances_and_prices_cache')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('balances_and_prices_cache',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('game_id', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('user_id', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('symbol', mysql.VARCHAR(length=255), nullable=True),
    sa.Column('timestamp', mysql.DOUBLE(asdecimal=True), nullable=True),
    sa.Column('balance', mysql.DOUBLE(asdecimal=True), nullable=True),
    sa.Column('price', mysql.DOUBLE(asdecimal=True), nullable=True),
    sa.Column('value', mysql.DOUBLE(asdecimal=True), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], name='balances_and_prices_cache_ibfk_1'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='balances_and_prices_cache_ibfk_2'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('ix_balances_and_prices_cache_timestamp', 'balances_and_prices_cache', ['timestamp'], unique=False)
    op.create_index('ix_balances_and_prices_cache_symbol', 'balances_and_prices_cache', ['symbol'], unique=False)
    op.create_index('balances_and_prices_game_user_timestamp_ix', 'balances_and_prices_cache', ['game_id', 'user_id', 'timestamp'], unique=False)
    # ### end Alembic commands ###
