"""
Add total_value column to customer_orders table (if not already present)
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Only add if not exists (idempotent)
    with op.batch_alter_table('customer_orders') as batch_op:
        batch_op.add_column(sa.Column('total_value', sa.Float(), nullable=True))

def downgrade():
    with op.batch_alter_table('customer_orders') as batch_op:
        batch_op.drop_column('total_value')
