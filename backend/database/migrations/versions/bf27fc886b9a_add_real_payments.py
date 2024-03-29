"""add real payments

Revision ID: bf27fc886b9a
Revises: 6a1fd042d869
Create Date: 2020-08-10 19:49:18.513707

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'bf27fc886b9a'
down_revision = '6a1fd042d869'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('payment_profiles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('processor', sa.Enum('paypal', name='processors'), nullable=True),
    sa.Column('uuid', sa.VARCHAR(length=255), nullable=True),
    sa.Column('payer_email', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.Float(precision=32), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_profiles_processor'), 'payment_profiles', ['processor'], unique=False)
    op.create_index(op.f('ix_payment_profiles_uuid'), 'payment_profiles', ['uuid'], unique=False)
    op.create_table('payments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('profile_id', sa.Integer(), nullable=True),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('winner_table_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.Enum('start', 'join', 'refund', 'sidebet', 'overall', name='paymenttypes'), nullable=True),
    sa.Column('amount', sa.Float(precision=32), nullable=True),
    sa.Column('currency', sa.Enum('usd', name='currencytypes'), nullable=True),
    sa.Column('direction', sa.Enum('inflow', 'outflow', name='paymentdirection'), nullable=True),
    sa.Column('timestamp', sa.Float(precision=32), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    sa.ForeignKeyConstraint(['profile_id'], ['payment_profiles.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['winner_table_id'], ['winners.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('games', sa.Column('stakes', sa.Enum('real', 'monopoly', name='gamestakes'), nullable=True))
    op.alter_column('users', 'provider',
               existing_type=mysql.ENUM('google', 'facebook', 'twitter', 'stockbets'),
               nullable=True)

    op.alter_column('game_status', 'status',
               existing_type=mysql.ENUM('pending', 'active', 'finished', 'expired'),
               nullable=False, type_=mysql.ENUM('pending', 'active', 'finished', 'expired', 'cancelled'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'provider',
               existing_type=mysql.ENUM('google', 'facebook', 'twitter', 'stockbets'),
               nullable=False)
    op.drop_column('games', 'stakes')
    op.drop_table('payments')
    op.drop_index(op.f('ix_payment_profiles_uuid'), table_name='payment_profiles')
    op.drop_index(op.f('ix_payment_profiles_processor'), table_name='payment_profiles')
    op.drop_table('payment_profiles')

    op.alter_column('game_status', 'status',
               existing_type=mysql.ENUM('pending', 'active', 'finished', 'expired', 'cancelled'),
               nullable=False, type_=mysql.ENUM('pending', 'active', 'finished', 'expired'))
    # ### end Alembic commands ###
