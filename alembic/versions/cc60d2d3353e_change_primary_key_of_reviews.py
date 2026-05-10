"""change primary key of reviews

Revision ID: cc60d2d3353e
Revises: 2137f6792cbc
Create Date: 2026-05-06 19:32:28.138565

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc60d2d3353e'
down_revision: Union[str, None] = '2137f6792cbc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('reviews_pkey', 'reviews', type_='primary')
    op.drop_column('reviews', 'id')
    op.create_primary_key('reviews_pkey', 'reviews', ['review_id'])
    pass


def downgrade() -> None:
    op.drop_constraint('reviews_pkey', 'reviews', type_='primary')
    op.add_column('reviews', sa.Column('id', sa.Integer, autoincrement=True, nullable=False))
    op.create_primary_key('reviews_pkey', 'reviews', ['id'])    
    pass
