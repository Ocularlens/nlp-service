"""add products table and review relationships

Revision ID: 7ca2a29246e0
Revises: 809a77b739c2
Create Date: 2026-07-05 14:00:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ca2a29246e0'
down_revision: Union[str, None] = '809a77b739c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### 1. Create the products table
    op.create_table(
        'products',
        sa.Column('product_id', sa.String(64), nullable=False),
        sa.Column('product_name', sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint('product_id'),
    )
    op.create_index('ix_products_product_id', 'products', ['product_id'], if_not_exists=True)
    op.create_index('ix_products_product_name', 'products', ['product_name'], unique=True, if_not_exists=True)

    # ### 2. Add product_id and mood columns (nullable initially for data migration)
    op.add_column('reviews', sa.Column('product_id', sa.String(64), nullable=True))
    op.create_index('ix_reviews_product_id', 'reviews', ['product_id'], if_not_exists=True)
    op.add_column('reviews', sa.Column('mood', sa.String(20), nullable=True))

    # ### 3. Migrate existing data
    conn = op.get_bind()

    # Create products from distinct review product names
    existing_products = conn.execute(
        sa.text("SELECT DISTINCT product FROM reviews WHERE product IS NOT NULL")
    ).fetchall()

    for (product_name,) in existing_products:
        if not product_name:
            continue
        pid = str(uuid.uuid4())
        upper_name = product_name.upper()
        # Insert product (ignore if already exists from a partial run)
        try:
            conn.execute(
                sa.text(
                    "INSERT INTO products (product_id, product_name) VALUES (:pid, :pn)"
                ),
                {"pid": pid, "pn": upper_name}
            )
        except Exception:
            existing = conn.execute(
                sa.text("SELECT product_id FROM products WHERE product_name = :pn"),
                {"pn": upper_name}
            ).fetchone()
            if existing:
                pid = existing[0]
            else:
                raise

        # Update reviews referencing this product
        conn.execute(
            sa.text("UPDATE reviews SET product_id = :pid WHERE product = :pn"),
            {"pid": pid, "pn": product_name}
        )

    # Set default mood for reviews without one
    conn.execute(
        sa.text("UPDATE reviews SET mood = 'neutral' WHERE mood IS NULL")
    )

    # ### 4. Drop old index on product column (outside batch, for PostgreSQL)
    op.drop_index('ix_reviews_product', table_name='reviews', if_exists=True)

    # ### 5. Recreate reviews table: drop product column, make new cols NOT NULL, add FK
    with op.batch_alter_table('reviews') as batch_op:
        batch_op.drop_column('product')
        batch_op.alter_column('product_id', nullable=False)
        batch_op.alter_column('mood', nullable=False)
        batch_op.create_foreign_key(
            'fk_reviews_product_id',
            'products',
            ['product_id'],
            ['product_id']
        )


def downgrade() -> None:
    # ### 1. Remove foreign key and restore product column
    with op.batch_alter_table('reviews') as batch_op:
        batch_op.drop_constraint('fk_reviews_product_id', type_='foreignkey')
        batch_op.add_column(sa.Column('product', sa.String(64), nullable=True))

    # ### 2. Populate product from the relationship
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE reviews SET product = ("
            "  SELECT LOWER(product_name) FROM products"
            "  WHERE products.product_id = reviews.product_id"
            ")"
        )
    )

    # Restore index on product column
    op.create_index('ix_reviews_product', 'reviews', ['product'], if_not_exists=True)

    # ### 3. Drop product_id, mood columns and their index
    op.drop_index('ix_reviews_product_id', table_name='reviews', if_exists=True)
    with op.batch_alter_table('reviews') as batch_op:
        batch_op.drop_column('mood')
        batch_op.drop_column('product_id')

    # ### 4. Drop products table
    op.drop_index('ix_products_product_name', table_name='products', if_exists=True)
    op.drop_index('ix_products_product_id', table_name='products', if_exists=True)
    op.drop_table('products')
