from alembic import context
from sqlalchemy import engine_from_config,pool
from app.config import settings
from app.db import Base
from app import models
c=context.config;c.set_main_option('sqlalchemy.url',settings.database_url)
if context.is_offline_mode():
 cxt=dict(url=settings.database_url,target_metadata=Base.metadata,literal_binds=True);context.configure(**cxt)
 with context.begin_transaction():context.run_migrations()
else:
 e=engine_from_config(c.get_section(c.config_ini_section),prefix='sqlalchemy.',poolclass=pool.NullPool)
 with e.connect() as conn:
  context.configure(connection=conn,target_metadata=Base.metadata)
  with context.begin_transaction():context.run_migrations()
