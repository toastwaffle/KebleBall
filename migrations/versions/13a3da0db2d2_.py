"""empty message

Revision ID: 13a3da0db2d2
Revises: fac5a30043f2
Create Date: 2016-03-05 15:27:34.482032

"""

# revision identifiers, used by Alembic.
revision = "13a3da0db2d2"
down_revision = "fac5a30043f2"

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("ticket", "name")
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column("ticket", sa.Column("name", mysql.VARCHAR(length=120), nullable=True))
    ### end Alembic commands ###
