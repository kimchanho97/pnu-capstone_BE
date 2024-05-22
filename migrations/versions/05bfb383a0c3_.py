"""empty message

Revision ID: 05bfb383a0c3
Revises: 0298cf34902a
Create Date: 2024-05-22 11:53:16.040193

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05bfb383a0c3'
down_revision = '0298cf34902a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Project', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deploy_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'Deploy', ['deploy_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Project', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('deploy_id')

    # ### end Alembic commands ###
