from datetime import datetime,timezone
from sqlalchemy import String,Integer,Float,Text,DateTime,Boolean,ForeignKey,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .database import Base
def now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(120)); email:Mapped[str]=mapped_column(String(180),unique=True,index=True)
    password:Mapped[str]=mapped_column(String(500)); role:Mapped[str]=mapped_column(String(20),default="candidate")
    city:Mapped[str]=mapped_column(String(120),default=""); phone:Mapped[str]=mapped_column(String(40),default="")
    title:Mapped[str]=mapped_column(String(150),default=""); salary:Mapped[float]=mapped_column(Float,default=0)
    remote:Mapped[str]=mapped_column(String(30),default="Qualquer"); plan:Mapped[str]=mapped_column(String(20),default="free")
    active:Mapped[bool]=mapped_column(Boolean,default=True); push_token:Mapped[str]=mapped_column(String(500),default="")
    created_at:Mapped[datetime]=mapped_column(DateTime,default=now)

class Company(Base):
    __tablename__="companies"
    id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),unique=True)
    name:Mapped[str]=mapped_column(String(180)); city:Mapped[str]=mapped_column(String(120),default="")
    description:Mapped[str]=mapped_column(Text,default=""); verified:Mapped[bool]=mapped_column(Boolean,default=False)

class Job(Base):
    __tablename__="jobs"
    id:Mapped[int]=mapped_column(primary_key=True); company_id:Mapped[int]=mapped_column(ForeignKey("companies.id"))
    title:Mapped[str]=mapped_column(String(180)); company:Mapped[str]=mapped_column(String(180)); city:Mapped[str]=mapped_column(String(120))
    salary_min:Mapped[float]=mapped_column(Float,default=0); salary_max:Mapped[float]=mapped_column(Float,default=0)
    modality:Mapped[str]=mapped_column(String(30),default="Presencial"); contract:Mapped[str]=mapped_column(String(40),default="CLT")
    level:Mapped[str]=mapped_column(String(60),default="Pleno"); description:Mapped[str]=mapped_column(Text,default="")
    requirements:Mapped[str]=mapped_column(Text,default=""); lat:Mapped[float]=mapped_column(Float,nullable=True); lon:Mapped[float]=mapped_column(Float,nullable=True)
    active:Mapped[bool]=mapped_column(Boolean,default=True); created_at:Mapped[datetime]=mapped_column(DateTime,default=now)

class Resume(Base):
    __tablename__="resumes"
    id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),unique=True)
    summary:Mapped[str]=mapped_column(Text,default=""); skills:Mapped[str]=mapped_column(Text,default="")
    experience:Mapped[str]=mapped_column(Text,default=""); education:Mapped[str]=mapped_column(Text,default="")
    file_name:Mapped[str]=mapped_column(String(255),default=""); file_data:Mapped[bytes|None]=mapped_column(nullable=True)

class Favorite(Base):
    __tablename__="favorites"
    id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id")); job_id:Mapped[int]=mapped_column(ForeignKey("jobs.id"))
    __table_args__=(UniqueConstraint("user_id","job_id"),)

class Application(Base):
    __tablename__="applications"
    id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id")); job_id:Mapped[int]=mapped_column(ForeignKey("jobs.id"))
    status:Mapped[str]=mapped_column(String(50),default="Enviada"); created_at:Mapped[datetime]=mapped_column(DateTime,default=now)
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=now)
    __table_args__=(UniqueConstraint("user_id","job_id"),)

class Event(Base):
    __tablename__="application_events"
    id:Mapped[int]=mapped_column(primary_key=True); application_id:Mapped[int]=mapped_column(ForeignKey("applications.id"))
    status:Mapped[str]=mapped_column(String(50)); note:Mapped[str]=mapped_column(Text,default=""); created_at:Mapped[datetime]=mapped_column(DateTime,default=now)

class Alert(Base):
    __tablename__="alerts"
    id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    keyword:Mapped[str]=mapped_column(String(150)); city:Mapped[str]=mapped_column(String(120),default="")
    modality:Mapped[str]=mapped_column(String(30),default=""); active:Mapped[bool]=mapped_column(Boolean,default=True)

class Message(Base):
    __tablename__="messages"
    id:Mapped[int]=mapped_column(primary_key=True); sender_id:Mapped[int]=mapped_column(ForeignKey("users.id")); receiver_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    body:Mapped[str]=mapped_column(Text); read:Mapped[bool]=mapped_column(Boolean,default=False); created_at:Mapped[datetime]=mapped_column(DateTime,default=now)

class Notification(Base):
    __tablename__="notifications"
    id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    title:Mapped[str]=mapped_column(String(180)); body:Mapped[str]=mapped_column(Text); kind:Mapped[str]=mapped_column(String(50),default="system")
    read:Mapped[bool]=mapped_column(Boolean,default=False); created_at:Mapped[datetime]=mapped_column(DateTime,default=now)
