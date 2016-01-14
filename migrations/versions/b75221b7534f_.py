"""empty message

Revision ID: b75221b7534f
Revises: 57bc3837370a
Create Date: 2016-01-11 19:56:43.653390

"""

# revision identifiers, used by Alembic.
revision = 'b75221b7534f'
down_revision = '57bc3837370a'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('postage', sa.Column('paid', sa.Boolean(), nullable=False))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('postage', 'paid')
    ### end Alembic commands ###
