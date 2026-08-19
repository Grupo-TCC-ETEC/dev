from datetime import date,timedelta,datetime,timezone
from io import BytesIO
import secrets
import qrcode
from decimal import Decimal
import jwt
from fastapi import FastAPI,Depends,HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from sqlalchemy import case,func,or_,select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import *
from app.security import verify,token,decode,hash_pwd
app=FastAPI(title='Estoque API',version='6.2.0');app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:4200'],allow_methods=['*'],allow_headers=['*'],allow_credentials=True);oauth=OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')
def current(t:str=Depends(oauth),s:Session=Depends(get_db)):
 try:e=decode(t)
 except jwt.InvalidTokenError:raise HTTPException(401,'Token inválido')
 u=s.scalar(select(User).where(User.email==e,User.active==True))
 if not u:raise HTTPException(401,'Usuário inválido')
 return u
def admin(u:User=Depends(current)):
 if u.role!=Role.admin:raise HTTPException(403,'Apenas administradores podem gerenciar usuários')
 return u
def dto(x):
 d={c.name:getattr(x,c.name) for c in x.__table__.columns}
 for k,v in list(d.items()):
  if hasattr(v,'value'):d[k]=v.value
 return d
@app.get('/health')
def health():return {'status':'ok','version':'6.2.0'}
@app.post('/api/v1/auth/login')
def login(f:OAuth2PasswordRequestForm=Depends(),s:Session=Depends(get_db)):
 u=s.scalar(select(User).where(User.email==f.username.lower()))
 if not u or not u.active or not verify(f.password,u.password_hash):raise HTTPException(401,'E-mail ou senha inválidos')
 return {'access_token':token(u.email),'token_type':'bearer'}
@app.get('/api/v1/auth/me')
def me(u:User=Depends(current)):return dto(u)
@app.get('/api/v1/users')
def users(s:Session=Depends(get_db),u:User=Depends(admin)):return [dto(x) for x in s.scalars(select(User).order_by(User.name))]
@app.post('/api/v1/users',status_code=201)
def create_user(d:dict,s:Session=Depends(get_db),u:User=Depends(admin)):
 if len(d.get('password',''))<8:raise HTTPException(422,'A senha deve ter pelo menos 8 caracteres')
 x=User(name=d['name'],email=d['email'].lower(),password_hash=hash_pwd(d['password']),role=Role(d.get('role','operator')),active=True);s.add(x)
 try:s.commit()
 except IntegrityError:s.rollback();raise HTTPException(409,'E-mail já cadastrado')
 s.refresh(x);return dto(x)
@app.patch('/api/v1/users/{uid}')
def update_user(uid:int,d:dict,s:Session=Depends(get_db),u:User=Depends(admin)):
 x=s.get(User,uid)
 if not x:raise HTTPException(404,'Usuário não encontrado')
 for k in ('name','active'):
  if k in d:setattr(x,k,d[k])
 if d.get('role'):x.role=Role(d['role'])
 if d.get('password'):
  if len(d['password'])<8:raise HTTPException(422,'A senha deve ter pelo menos 8 caracteres')
  x.password_hash=hash_pwd(d['password'])
 s.commit();s.refresh(x);return dto(x)
@app.get('/api/v1/products')
def products(search:str='',s:Session=Depends(get_db),u:User=Depends(current)):
 q=select(Product).where(Product.active==True)
 if search:q=q.where(or_(Product.name.ilike(f'%{search}%'),Product.sku.ilike(f'%{search}%')))
 return [dto(x) for x in s.scalars(q.order_by(Product.name))]
@app.post('/api/v1/products',status_code=201)
def add_product(d:dict,s:Session=Depends(get_db),u:User=Depends(current)):
 x=Product(**{k:v for k,v in d.items() if k in {'name','sku','category','unit','minimum_stock','controls_expiration'}});s.add(x);s.commit();s.refresh(x);return dto(x)
@app.patch('/api/v1/products/{pid}')
def edit_product(pid:int,d:dict,s:Session=Depends(get_db),u:User=Depends(current)):
 x=s.get(Product,pid)
 if not x:raise HTTPException(404,'Produto não encontrado')
 for k,v in d.items():
  if k in {'name','sku','category','unit','minimum_stock','controls_expiration','active'}:setattr(x,k,v)
 s.commit();s.refresh(x);return dto(x)
@app.get('/api/v1/batches')
def batches(s:Session=Depends(get_db),u:User=Depends(current)):return [dto(x) for x in s.scalars(select(Batch).order_by(Batch.expiration_date,Batch.received_at))]
@app.post('/api/v1/stock/entries',status_code=201)
def entry(d:dict,s:Session=Depends(get_db),u:User=Depends(current)):
 p=s.get(Product,d['product_id'])
 if not p:raise HTTPException(404,'Produto não encontrado')
 if p.controls_expiration and not d.get('expiration_date'):raise HTTPException(422,'Informe a validade')
 qty=Decimal(str(d['quantity']))
 if qty != int(qty) or qty < 1:raise HTTPException(422,'Para etiquetas individuais, informe uma quantidade inteira maior que zero')
 x=Batch(product_id=p.id,batch_number=d['batch_number'],initial_quantity=qty,current_quantity=qty,manufacture_date=d.get('manufacture_date') or None,expiration_date=d.get('expiration_date') or None,supplier=d.get('supplier') or None,unit_cost=d.get('unit_cost') or None,qr_token=secrets.token_urlsafe(24));s.add(x);s.flush()
 for n in range(1,int(qty)+1):
  s.add(StockItem(batch_id=x.id,serial_number=f'{x.batch_number}-{n:04d}-{secrets.token_hex(3).upper()}',qr_token=secrets.token_urlsafe(24),active=True))
 s.add(Movement(product_id=p.id,batch_id=x.id,user_id=u.id,movement_type=Move.entry,quantity=qty,reason='Entrada',notes=d.get('notes')));s.commit();s.refresh(x);return dto(x)
@app.post('/api/v1/stock/consume',status_code=201)
def consume(d:dict,s:Session=Depends(get_db),u:User=Depends(current)):
 q=select(Batch).where(Batch.product_id==d['product_id'],Batch.current_quantity>0,or_(Batch.expiration_date==None,Batch.expiration_date>=date.today())).order_by(case((Batch.expiration_date==None,1),else_=0),Batch.expiration_date,Batch.received_at).with_for_update();bs=list(s.scalars(q));need=Decimal(str(d['quantity']));available=sum((b.current_quantity for b in bs),Decimal(0))
 if available<need:raise HTTPException(409,f'Estoque insuficiente. Disponível: {available}')
 out=[]
 for b in bs:
  if need<=0:break
  amount=min(need,b.current_quantity);b.current_quantity-=amount;m=Movement(product_id=d['product_id'],batch_id=b.id,user_id=u.id,movement_type=Move.consumption,quantity=amount,reason='Consumo',department=d.get('department'),notes=d.get('notes'));s.add(m);out.append(m);need-=amount
 s.commit();return [dto(x) for x in out]
@app.post('/api/v1/stock/adjustments',status_code=201)
def adjustment(d:dict,s:Session=Depends(get_db),u:User=Depends(current)):
 b=s.scalar(select(Batch).where(Batch.id==d['batch_id']).with_for_update());qty=Decimal(str(d['quantity']))
 if not b:raise HTTPException(404,'Lote não encontrado')
 if not d['positive'] and b.current_quantity<qty:raise HTTPException(409,'Saldo insuficiente')
 b.current_quantity+=qty if d['positive'] else -qty;m=Movement(product_id=b.product_id,batch_id=b.id,user_id=u.id,movement_type=Move.positive_adjustment if d['positive'] else Move.negative_adjustment,quantity=qty,reason=d['reason']);s.add(m);s.commit();return dto(m)
@app.post('/api/v1/stock/losses',status_code=201)
def loss(d:dict,s:Session=Depends(get_db),u:User=Depends(current)):
 b=s.scalar(select(Batch).where(Batch.id==d['batch_id']).with_for_update());qty=Decimal(str(d['quantity']))
 if not b or b.current_quantity<qty:raise HTTPException(409,'Lote inexistente ou saldo insuficiente')
 b.current_quantity-=qty;m=Movement(product_id=b.product_id,batch_id=b.id,user_id=u.id,movement_type=Move.expired if d.get('expired') else Move.loss,quantity=qty,reason=d['reason']);s.add(m);s.commit();return dto(m)
@app.get('/api/v1/stock/movements')
def movements(s:Session=Depends(get_db),u:User=Depends(current)):return [dto(x) for x in s.scalars(select(Movement).order_by(Movement.created_at.desc()).limit(500))]
@app.get('/api/v1/alerts')
def alerts(s:Session=Depends(get_db),u:User=Depends(current)):
 t=date.today();return {'expired':[dto(x) for x in s.scalars(select(Batch).where(Batch.current_quantity>0,Batch.expiration_date<t))],'expiring':[dto(x) for x in s.scalars(select(Batch).where(Batch.current_quantity>0,Batch.expiration_date.between(t,t+timedelta(days=30))))]}
@app.get('/api/v1/dashboard')
def dashboard(s:Session=Depends(get_db),u:User=Depends(current)):
 ps=list(s.scalars(select(Product).where(Product.active==True)));bal={p.id:s.scalar(select(func.coalesce(func.sum(Batch.current_quantity),0)).where(Batch.product_id==p.id)) for p in ps};t=date.today();return {'products':len(ps),'stock':str(sum(bal.values(),Decimal(0))),'low':sum(bal[p.id]<p.minimum_stock for p in ps),'alerts':s.scalar(select(func.count()).select_from(Batch).where(Batch.current_quantity>0,Batch.expiration_date<=t+timedelta(days=30)))}


def ensure_token(batch:Batch,s:Session):
 if not batch.qr_token:
  batch.qr_token=secrets.token_urlsafe(24);s.commit();s.refresh(batch)
 return batch.qr_token

@app.get('/api/v1/batches/{batch_id}/qr')
def batch_qr(batch_id:int,s:Session=Depends(get_db),u:User=Depends(current)):
 b=s.get(Batch,batch_id)
 if not b:raise HTTPException(404,'Lote não encontrado')
 token=ensure_token(b,s);img=qrcode.make('ESTOQUE:'+token);buf=BytesIO();img.save(buf,format='PNG');buf.seek(0)
 return StreamingResponse(buf,media_type='image/png',headers={'Cache-Control':'no-store'})

@app.get('/api/v1/batches/{batch_id}/label')
def batch_label(batch_id:int,s:Session=Depends(get_db),u:User=Depends(current)):
 b=s.get(Batch,batch_id)
 if not b:raise HTTPException(404,'Lote não encontrado')
 ensure_token(b,s);p=s.get(Product,b.product_id)
 return {'batch':dto(b),'product':dto(p)}

@app.get('/api/v1/scan/{token}')
def scan_token(token:str,s:Session=Depends(get_db),u:User=Depends(current)):
 token=token.removeprefix('ESTOQUE:').strip();b=s.scalar(select(Batch).where(Batch.qr_token==token))
 if not b:raise HTTPException(404,'QR Code não encontrado')
 p=s.get(Product,b.product_id)
 return {'product':dto(p),'batch':dto(b)}


def sync_items(s:Session):
 batches=list(s.scalars(select(Batch)))
 changed=False
 for b in batches:
  target=max(0,int(b.current_quantity))
  existing=list(s.scalars(select(StockItem).where(StockItem.batch_id==b.id).order_by(StockItem.id)))
  while len(existing)<target:
   n=len(existing)+1;item=StockItem(batch_id=b.id,serial_number=f'{b.batch_number}-{n:04d}-{secrets.token_hex(3).upper()}',qr_token=secrets.token_urlsafe(24),active=True);s.add(item);existing.append(item);changed=True
  available=[item for item in existing if item.consumed_at is None]
  for pos,item in enumerate(available):
   should=pos<target
   if item.active!=should:item.active=should;changed=True
 if changed:s.commit()

@app.get('/api/v1/items')
def items(s:Session=Depends(get_db),u:User=Depends(current)):
 sync_items(s);rows=s.execute(select(StockItem,Batch,Product).join(Batch,StockItem.batch_id==Batch.id).join(Product,Batch.product_id==Product.id).order_by(Product.name,StockItem.id)).all()
 return [{'item':dto(i),'batch':dto(b),'product':dto(p)} for i,b,p in rows if i.active]

@app.get('/api/v1/items/{item_id}/label')
def item_label(item_id:int,s:Session=Depends(get_db),u:User=Depends(current)):
 item=s.get(StockItem,item_id)
 if not item:raise HTTPException(404,'Item individual não encontrado. Atualize a tela e tente novamente.')
 b=s.get(Batch,item.batch_id);p=s.get(Product,b.product_id)
 return {'item':dto(item),'batch':dto(b),'product':dto(p)}

@app.get('/api/v1/items/{item_id}/qr')
def item_qr(item_id:int,s:Session=Depends(get_db),u:User=Depends(current)):
 item=s.get(StockItem,item_id)
 if not item:raise HTTPException(404,'Item individual não encontrado')
 img=qrcode.make('ITEM:'+item.qr_token);buf=BytesIO();img.save(buf,format='PNG');buf.seek(0)
 return StreamingResponse(buf,media_type='image/png',headers={'Cache-Control':'no-store'})

@app.get('/api/v1/items/scan/{token}')
def scan_item(token:str,s:Session=Depends(get_db),u:User=Depends(current)):
 token=token.removeprefix('ITEM:').strip();item=s.scalar(select(StockItem).where(StockItem.qr_token==token))
 if not item:raise HTTPException(404,'QR Code individual não encontrado')
 b=s.get(Batch,item.batch_id);p=s.get(Product,b.product_id)
 return {'item':dto(item),'batch':dto(b),'product':dto(p)}


@app.post('/api/v1/items/{item_id}/consume')
def consume_item(item_id:int,d:dict,s:Session=Depends(get_db),u:User=Depends(current)):
 item=s.scalar(select(StockItem).where(StockItem.id==item_id).with_for_update())
 if not item:raise HTTPException(404,'Item individual não encontrado')
 if not item.active or item.consumed_at is not None:raise HTTPException(409,'Este item já foi consumido')
 batch=s.scalar(select(Batch).where(Batch.id==item.batch_id).with_for_update())
 if not batch or batch.current_quantity<1:raise HTTPException(409,'O lote não possui saldo disponível')
 item.active=False;item.consumed_at=datetime.now(timezone.utc);item.consumed_by=u.id;item.department=d.get('department') or None;item.consumption_notes=d.get('notes') or None
 batch.current_quantity-=Decimal('1')
 movement=Movement(product_id=batch.product_id,batch_id=batch.id,user_id=u.id,movement_type=Move.consumption,quantity=Decimal('1'),reason='Consumo por QR Code',department=item.department,notes=item.consumption_notes or f'Item {item.serial_number}')
 s.add(movement);s.commit();s.refresh(movement)
 return {'message':'Produto marcado como consumido','item':dto(item),'movement':dto(movement)}
