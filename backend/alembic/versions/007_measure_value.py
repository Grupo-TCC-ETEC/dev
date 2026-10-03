from alembic import op
import sqlalchemy as sa
revision='007';down_revision='006';branch_labels=None;depends_on=None
def upgrade():
 op.add_column('products',sa.Column('measure_value',sa.Numeric(14,3),nullable=False,server_default='1'))
def downgrade():
 op.drop_column('products','measure_value')
