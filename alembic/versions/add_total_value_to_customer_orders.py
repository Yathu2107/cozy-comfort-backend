"""
Add total_value column to customer_orders table
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('customer_orders', sa.Column('total_value', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('customer_orders', 'total_value')
