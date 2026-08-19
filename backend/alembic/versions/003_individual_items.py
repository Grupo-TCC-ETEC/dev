from alembic import op
import sqlalchemy as sa
revision='003'
down_revision='002'
branch_labels=None
depends_on=None
def upgrade():
 op.create_table('stock_items',sa.Column('id',sa.Integer,primary_key=True),sa.Column('batch_id',sa.Integer,sa.ForeignKey('batches.id'),nullable=False),sa.Column('serial_number',sa.String(80),nullable=False,unique=True),sa.Column('qr_token',sa.String(64),nullable=False,unique=True),sa.Column('active',sa.Boolean,nullable=False,server_default=sa.true()),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now()))
 op.create_index('ix_stock_items_batch_id','stock_items',['batch_id'])
 op.create_index('ix_stock_items_serial_number','stock_items',['serial_number'],unique=True)
 op.create_index('ix_stock_items_qr_token','stock_items',['qr_token'],unique=True)
def downgrade():
 op.drop_table('stock_items')
