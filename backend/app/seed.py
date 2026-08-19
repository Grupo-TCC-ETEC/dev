from sqlalchemy import select
from app.config import settings
from app.db import SessionLocal
from app.models import User,Role
from app.security import hash_pwd
with SessionLocal() as s:
 if not s.scalar(select(User).where(User.email==settings.admin_email.lower())):
  s.add(User(name=settings.admin_name,email=settings.admin_email.lower(),password_hash=hash_pwd(settings.admin_password),role=Role.admin));s.commit()
