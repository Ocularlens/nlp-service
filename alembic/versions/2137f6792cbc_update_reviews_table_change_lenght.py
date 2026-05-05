"""update reviews table: change lenght

Revision ID: 2137f6792cbc
Revises: 36cc95b57ef9
Create Date: 2026-05-05 10:20:41.453782

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2137f6792cbc'
down_revision: Union[str, None] = '36cc95b57ef9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('reviews', 'product',
                    type_=sa.String(length=64),
                    nullable=False,
                    index=True)
    pass


def downgrade() -> None:
    op.alter_column('reviews', 'product',
                    type_=sa.String(length=12),
                    nullable=False,
                    index=True)
    pass
