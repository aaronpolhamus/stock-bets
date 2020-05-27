"""initial data model

Revision ID: d58e9f252421
Revises: 
Create Date: 2020-05-24 18:26:11.435007

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd58e9f252421'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('prices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol', sa.Text(), nullable=True),
    sa.Column('price', sa.Float(precision=32), nullable=True),
    sa.Column('timestamp', sa.Float(precision=32), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('symbols',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol', sa.Text(), nullable=True),
    sa.Column('name', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('email', sa.Text(), nullable=True),
    sa.Column('profile_pic', sa.Text(), nullable=True),
    sa.Column('username', sa.Text(), nullable=True),
    sa.Column('created_at', sa.Float(precision=32), nullable=True),
    sa.Column('provider', sa.Enum('google', 'facebook', 'twitter', name='oauthproviders'), nullable=True),
    sa.Column('resource_uuid', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('friends',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('requester_id', sa.Integer(), nullable=True),
    sa.Column('invited_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('invited', 'accepted', 'declined', name='friendstatuses'), nullable=True),
    sa.Column('timestamp', sa.Float(precision=32), nullable=True),
    sa.ForeignKeyConstraint(['invited_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('games',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('creator_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.Text(), nullable=True),
    sa.Column('mode', sa.Enum('return_weighted', 'consolation_prize', 'winner_takes_all', name='gamemodes'), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('buy_in', sa.Float(precision=32), nullable=True),
    sa.Column('n_rebuys', sa.Integer(), nullable=True),
    sa.Column('benchmark', sa.Enum('return_ratio', 'sharpe_ratio', name='benchmarks'), nullable=True),
    sa.Column('side_bets_perc', sa.Float(precision=32), nullable=True),
    sa.Column('side_bets_period', sa.Enum('weekly', 'monthly', name='sidebetperiods'), nullable=True),
    sa.Column('invite_window', sa.Float(precision=32), nullable=True),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('game_invites',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('invited', 'joined', 'declined', 'expired', name='gameinvitestatustypes'), nullable=True),
    sa.Column('timestamp', sa.Float(precision=32), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('game_status',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('pending', 'active', 'finished', 'expired', name='gamestatustypes'), nullable=True),
    sa.Column('users', sa.JSON(), nullable=True),
    sa.Column('timestamp', sa.Float(precision=32), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('symbol', sa.Text(), nullable=True),
    sa.Column('buy_or_sell', sa.Enum('buy', 'sell', name='buyorsell'), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.Column('price', sa.Float(precision=32), nullable=True),
    sa.Column('order_type', sa.Enum('market', 'limit', 'stop', name='ordertypes'), nullable=True),
    sa.Column('time_in_force', sa.Enum('day', 'until_cancelled', name='timeinforce'), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('order_status',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.Float(precision=32), nullable=True),
    sa.Column('status', sa.Enum('pending', 'fulfilled', 'cancelled', 'expired', name='orderstatustypes'), nullable=True),
    sa.Column('clear_price', sa.Float(precision=32), nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('game_balances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('order_status_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.Float(precision=32), nullable=True),
    sa.Column('balance_type', sa.Enum('virtual_cash', 'virtual_stock', name='gamebalancetypes'), nullable=True),
    sa.Column('balance', sa.Float(precision=32), nullable=True),
    sa.Column('symbol', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    sa.ForeignKeyConstraint(['order_status_id'], ['order_status.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('game_balances')
    op.drop_table('order_status')
    op.drop_table('orders')
    op.drop_table('game_status')
    op.drop_table('game_invites')
    op.drop_table('games')
    op.drop_table('friends')
    op.drop_table('users')
    op.drop_table('symbols')
    op.drop_table('prices')
    # ### end Alembic commands ###
