from alembic import op
import sqlalchemy as sa
revision="002"
down_revision="001"
branch_labels=None
depends_on=None
def upgrade():
 op.add_column("batches",sa.Column("qr_token",sa.String(64),nullable=True))
 op.create_index("ix_batches_qr_token","batches",["qr_token"],unique=True)
def downgrade():
 op.drop_index("ix_batches_qr_token",table_name="batches")
 op.drop_column("batches","qr_token")
