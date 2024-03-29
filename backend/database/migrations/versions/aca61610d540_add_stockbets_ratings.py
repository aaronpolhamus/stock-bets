"""add stockbets ratings

Revision ID: aca61610d540
Revises: 64208ffde6f0
Create Date: 2020-09-28 02:26:20.252705

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aca61610d540'
down_revision = '64208ffde6f0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('stockbets_rating',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('index_symbol', sa.VARCHAR(length=255), nullable=True),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('rating', sa.Float(precision=32), nullable=True),
    sa.Column('update_type', sa.Enum('sign_up', 'game_end', name='eventtypes'), nullable=True),
    sa.Column('timestamp', sa.Float(precision=32), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stockbets_rating_index_symbol'), 'stockbets_rating', ['index_symbol'], unique=False)
    op.create_index(op.f('ix_stockbets_rating_user_id'), 'stockbets_rating', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_stockbets_rating_user_id'), table_name='stockbets_rating')
    op.drop_index(op.f('ix_stockbets_rating_index_symbol'), table_name='stockbets_rating')
    op.drop_table('stockbets_rating')
    # ### end Alembic commands ###
