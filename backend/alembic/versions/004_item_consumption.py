from alembic import op
import sqlalchemy as sa
revision='004'
down_revision='003'
branch_labels=None
depends_on=None
def upgrade():
 op.add_column('stock_items',sa.Column('consumed_at',sa.DateTime(timezone=True),nullable=True))
 op.add_column('stock_items',sa.Column('consumed_by',sa.Integer,sa.ForeignKey('users.id'),nullable=True))
 op.add_column('stock_items',sa.Column('department',sa.String(120),nullable=True))
 op.add_column('stock_items',sa.Column('consumption_notes',sa.Text,nullable=True))
def downgrade():
 op.drop_column('stock_items','consumption_notes')
 op.drop_column('stock_items','department')
 op.drop_column('stock_items','consumed_by')
 op.drop_column('stock_items','consumed_at')
