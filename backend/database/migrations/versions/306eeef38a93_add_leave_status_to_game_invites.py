"""add leave status to game invites

Revision ID: 306eeef38a93
Revises: 7c611bf6e432
Create Date: 2020-07-21 22:01:26.530307

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '306eeef38a93'
down_revision = '7c611bf6e432'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('external_invites', 'timestamp',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('friends', 'timestamp',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('game_balances', 'balance',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('game_balances', 'timestamp',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('game_invites', 'timestamp',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('game_status', 'timestamp',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('games', 'buy_in',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('games', 'invite_window',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('games', 'side_bets_perc',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('indexes', 'timestamp',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('indexes', 'value',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('order_status', 'clear_price',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('order_status', 'timestamp',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('orders', 'price',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('prices', 'price',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('prices', 'timestamp',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('users', 'created_at',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('winners', 'end_time',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('winners', 'payout',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('winners', 'score',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('winners', 'start_time',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)
    op.alter_column('winners', 'timestamp',
               existing_type=mysql.DOUBLE(asdecimal=True),
               type_=sa.Float(precision=32),
               existing_nullable=True)

    # from https://gitpress.io/c/1484/mysql-example-alembic_change_enum
    op.alter_column('game_invites', 'status',
               existing_type=mysql.ENUM('invited', 'joined', 'declined', 'expired'),
               nullable=False, type_=mysql.ENUM('invited', 'joined', 'declined', 'expired', 'left'))


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('winners', 'timestamp',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('winners', 'start_time',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('winners', 'score',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('winners', 'payout',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('winners', 'end_time',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('users', 'created_at',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('prices', 'timestamp',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('prices', 'price',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('orders', 'price',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('order_status', 'timestamp',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('order_status', 'clear_price',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('indexes', 'value',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('indexes', 'timestamp',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('games', 'side_bets_perc',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('games', 'invite_window',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('games', 'buy_in',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('game_status', 'timestamp',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('game_invites', 'timestamp',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('game_balances', 'timestamp',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('game_balances', 'balance',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('friends', 'timestamp',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)
    op.alter_column('external_invites', 'timestamp',
               existing_type=sa.Float(precision=32),
               type_=mysql.DOUBLE(asdecimal=True),
               existing_nullable=True)

    op.alter_column('game_invites', 'status',
               existing_type=mysql.ENUM('invited', 'joined', 'declined', 'expired', 'left'),
               nullable=False, type_=mysql.ENUM('invited', 'joined', 'declined', 'expired'))
    # ### end Alembic commands ###
