"""test table

Revision ID: 480cd5ab053f
Revises: 2af876e0224b
Create Date: 2026-05-05 10:05:47.523750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '480cd5ab053f'
down_revision: Union[str, None] = '2af876e0224b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'test',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False),
    )
    pass


def downgrade() -> None:
    op.drop_table('test')
    pass
