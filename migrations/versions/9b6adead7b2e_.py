"""empty message

Revision ID: 9b6adead7b2e
Revises: ea5cf08c85a5
Create Date: 2019-07-01 20:11:15.120994

"""

# revision identifiers, used by Alembic.
revision = '9b6adead7b2e'
down_revision = 'ea5cf08c85a5'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('affiliation_list_entry', 'email',
               existing_type=mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=120),
               nullable=True)
    op.create_unique_constraint(None, 'affiliation_list_entry', ['affiliation_reference'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'affiliation_list_entry', type_='unique')
    op.alter_column('affiliation_list_entry', 'email',
               existing_type=mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=120),
               nullable=False)
    ### end Alembic commands ###
