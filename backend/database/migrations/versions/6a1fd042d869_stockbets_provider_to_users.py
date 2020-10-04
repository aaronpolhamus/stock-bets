"""stockbets provider to users

Revision ID: 6a1fd042d869
Revises: ad651650f60c
Create Date: 2020-08-06 23:42:58.238174

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = '6a1fd042d869'
down_revision = '4b2b5e6d761d'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('users', 'provider', existing_type=mysql.ENUM('google', 'facebook', 'twitter'),
                    nullable=False, type_=mysql.ENUM('google', 'facebook', 'twitter', 'stockbets'))

    op.alter_column('users', 'email', existing_type=sa.Text, type_=sa.VARCHAR(length=255),
                    existing_nullable=True)
    op.alter_column('users', 'name', existing_type=sa.Text, type_=sa.VARCHAR(length=255),
                    existing_nullable=True)
    op.alter_column('users', 'username', existing_type=sa.Text, type_=sa.VARCHAR(length=255),
                    existing_nullable=True)
    op.alter_column('users', 'resource_uuid', existing_type=sa.Text, type_=sa.VARCHAR(length=255),
                    existing_nullable=True)

    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('password', sa.Text(), nullable=True))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_name'), 'users', ['name'], unique=False)
    op.create_index(op.f('ix_users_resource_uuid'), 'users', ['resource_uuid'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    op.alter_column('users', 'provider', existing_type=mysql.ENUM('google', 'facebook', 'twitter', 'stockbets'),
                    nullable=False, type_=mysql.ENUM('google', 'facebook', 'twitter'))

    op.alter_column('users', 'email', existing_type=sa.VARCHAR(length=255), type_=sa.Text,
                    existing_nullable=True)
    op.alter_column('users', 'name', existing_type=sa.VARCHAR(length=255), type_=sa.Text,
                    existing_nullable=True)
    op.alter_column('users', 'username', existing_type=sa.VARCHAR(length=255), type_=sa.Text,
                    existing_nullable=True)
    op.alter_column('users', 'resource_uuid', existing_type=sa.VARCHAR(length=255), type_=sa.Text,
                    existing_nullable=True)

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_resource_uuid'), table_name='users')
    op.drop_index(op.f('ix_users_name'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'password')
    # ### end Alembic commands ###
