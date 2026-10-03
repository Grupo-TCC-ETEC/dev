from alembic import op
import sqlalchemy as sa
revision='005';down_revision='004';branch_labels=None;depends_on=None
def upgrade():
 op.create_table('suppliers',sa.Column('id',sa.Integer,primary_key=True),sa.Column('name',sa.String(150),nullable=False,unique=True),sa.Column('document',sa.String(30)),sa.Column('phone',sa.String(30)),sa.Column('email',sa.String(255)),sa.Column('active',sa.Boolean,nullable=False,server_default=sa.true()),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now()))
 op.add_column('products',sa.Column('supplier_id',sa.Integer(),nullable=True));op.create_foreign_key('fk_products_supplier','products','suppliers',['supplier_id'],['id'])
def downgrade():
 op.drop_constraint('fk_products_supplier','products',type_='foreignkey');op.drop_column('products','supplier_id');op.drop_table('suppliers')
