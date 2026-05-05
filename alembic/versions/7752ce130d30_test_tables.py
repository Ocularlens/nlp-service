"""test tables

Revision ID: 7752ce130d30
Revises: 480cd5ab053f
Create Date: 2026-05-05 10:07:34.578981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7752ce130d30'
down_revision: Union[str, None] = '480cd5ab053f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('test')
    pass


def downgrade() -> None:
    op.create_table(
        'test',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False),
    )
    pass
