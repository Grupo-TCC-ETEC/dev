from alembic import op
import sqlalchemy as sa
revision='006';down_revision='005';branch_labels=None;depends_on=None
def upgrade():
 op.execute(sa.text('UPDATE products SET controls_expiration = true, minimum_stock = 0'))
def downgrade():
 pass
