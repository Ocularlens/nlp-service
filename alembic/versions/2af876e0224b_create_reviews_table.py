"""create reviews table

Revision ID: 2af876e0224b
Revises: 
Create Date: 2026-05-04 13:45:50.873298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2af876e0224b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('review_id', sa.String(25), nullable=False, unique=True, index=True),
        sa.Column('product', sa.String(12), nullable=False, index=True),
        sa.Column('review_text', sa.String(120), nullable=False),
        sa.Column('rating', sa.Integer, nullable=True),
    )

def downgrade() -> None:
    op.drop_table('reviews')
