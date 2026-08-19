import enum
from datetime import date,datetime
from decimal import Decimal
from sqlalchemy import Boolean,Date,DateTime,Enum,ForeignKey,Numeric,String,Text,func
from sqlalchemy.orm import Mapped,mapped_column
from app.db import Base
class Role(str,enum.Enum):admin='admin';manager='manager';operator='operator'
class Move(str,enum.Enum):entry='entry';consumption='consumption';positive_adjustment='positive_adjustment';negative_adjustment='negative_adjustment';loss='loss';expired='expired'
class User(Base):
 __tablename__='users';id:Mapped[int]=mapped_column(primary_key=True);name:Mapped[str]=mapped_column(String(120));email:Mapped[str]=mapped_column(String(255),unique=True);password_hash:Mapped[str]=mapped_column(String(255));role:Mapped[Role]=mapped_column(Enum(Role,name='userrole'));active:Mapped[bool]=mapped_column(Boolean,default=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
class Product(Base):
 __tablename__='products';id:Mapped[int]=mapped_column(primary_key=True);name:Mapped[str]=mapped_column(String(150));sku:Mapped[str|None]=mapped_column(String(80),unique=True);category:Mapped[str|None]=mapped_column(String(100));unit:Mapped[str]=mapped_column(String(30));minimum_stock:Mapped[Decimal]=mapped_column(Numeric(14,3),default=0);controls_expiration:Mapped[bool]=mapped_column(Boolean,default=True);active:Mapped[bool]=mapped_column(Boolean,default=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now());updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now())
class Batch(Base):
 __tablename__='batches';id:Mapped[int]=mapped_column(primary_key=True);product_id:Mapped[int]=mapped_column(ForeignKey('products.id'));batch_number:Mapped[str]=mapped_column(String(80));initial_quantity:Mapped[Decimal]=mapped_column(Numeric(14,3));current_quantity:Mapped[Decimal]=mapped_column(Numeric(14,3));manufacture_date:Mapped[date|None]=mapped_column(Date);expiration_date:Mapped[date|None]=mapped_column(Date);received_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now());supplier:Mapped[str|None]=mapped_column(String(160));unit_cost:Mapped[Decimal|None]=mapped_column(Numeric(14,2));qr_token:Mapped[str|None]=mapped_column(String(64),unique=True,index=True)
class Movement(Base):
 __tablename__='stock_movements';id:Mapped[int]=mapped_column(primary_key=True);product_id:Mapped[int]=mapped_column(ForeignKey('products.id'));batch_id:Mapped[int]=mapped_column(ForeignKey('batches.id'));user_id:Mapped[int]=mapped_column(ForeignKey('users.id'));movement_type:Mapped[Move]=mapped_column(Enum(Move,name='movementtype'));quantity:Mapped[Decimal]=mapped_column(Numeric(14,3));reason:Mapped[str|None]=mapped_column(String(200));department:Mapped[str|None]=mapped_column(String(120));notes:Mapped[str|None]=mapped_column(Text);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class StockItem(Base):
 __tablename__='stock_items';id:Mapped[int]=mapped_column(primary_key=True);batch_id:Mapped[int]=mapped_column(ForeignKey('batches.id'),index=True);serial_number:Mapped[str]=mapped_column(String(80),unique=True,index=True);qr_token:Mapped[str]=mapped_column(String(64),unique=True,index=True);active:Mapped[bool]=mapped_column(Boolean,default=True);created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now());consumed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True));consumed_by:Mapped[int|None]=mapped_column(ForeignKey('users.id'));department:Mapped[str|None]=mapped_column(String(120));consumption_notes:Mapped[str|None]=mapped_column(Text)
