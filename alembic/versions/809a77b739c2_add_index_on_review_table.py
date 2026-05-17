"""add index on review table

Revision ID: 809a77b739c2
Revises: cc60d2d3353e
Create Date: 2026-05-17 21:01:55.018272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '809a77b739c2'
down_revision: Union[str, None] = 'cc60d2d3353e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_reviews_product', 'reviews', ['product'], if_not_exists=True)
    op.create_index('ix_reviews_rating', 'reviews', ['rating'], if_not_exists=True)
    op.create_index('ix_reviews_review_text', 'reviews', ['review_text'], if_not_exists=True)
    pass


def downgrade() -> None:
    op.drop_index('ix_reviews_product', table_name='reviews', if_exists=True)
    op.drop_index('ix_reviews_rating', table_name='reviews', if_exists=True)
    op.drop_index('ix_reviews_review_text', table_name='reviews', if_exists=True)
    pass
