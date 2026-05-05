"""update review table: change length of review_id

Revision ID: 36cc95b57ef9
Revises: 7752ce130d30
Create Date: 2026-05-05 10:12:11.339225

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36cc95b57ef9'
down_revision: Union[str, None] = '7752ce130d30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('reviews', 'review_id',
                    type_=sa.String(length=64), 
                    nullable=False, 
                    unique=True, 
                    index=True)
    pass


def downgrade() -> None:
    op.alter_column('reviews', 'review_id', 
                    type=sa.String(length=25), 
                    nullable=False, 
                    unique=True, 
                    index=True)
    pass
