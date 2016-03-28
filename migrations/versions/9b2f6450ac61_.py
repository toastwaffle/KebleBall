"""empty message

Revision ID: 9b2f6450ac61
Revises: 4c5a72833c0b
Create Date: 2016-03-28 17:10:34.920798

"""

# revision identifiers, used by Alembic.
revision = '9b2f6450ac61'
down_revision = '4c5a72833c0b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('postage', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'postage', 'user', ['owner_id'], ['object_id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'postage', type_='foreignkey')
    op.drop_column('postage', 'owner_id')
    ### end Alembic commands ###
