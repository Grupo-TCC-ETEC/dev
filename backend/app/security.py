from datetime import datetime,timedelta,timezone
import jwt
from pwdlib import PasswordHash
from app.config import settings
ph=PasswordHash.recommended()
def hash_pwd(x):return ph.hash(x)
def verify(x,h):return ph.verify(x,h)
def token(x):return jwt.encode({'sub':x,'exp':datetime.now(timezone.utc)+timedelta(hours=8)},settings.secret_key,algorithm='HS256')
def decode(x):return jwt.decode(x,settings.secret_key,algorithms=['HS256'])['sub']
