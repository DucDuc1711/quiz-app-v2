"""Remove allow_retake from Quiz

Revision ID: 2f3b8e4c9a1d
Revises: fd1ea53b1bde
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f3b8e4c9a1d'
down_revision = 'fd1ea53b1bde'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.drop_column('allow_retake')


def downgrade():
    with op.batch_alter_table('quizzes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('allow_retake', sa.Boolean(), nullable=False, server_default=sa.false()))