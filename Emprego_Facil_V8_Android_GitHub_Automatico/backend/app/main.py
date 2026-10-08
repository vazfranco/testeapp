from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import APP_VERSION,CORS_ORIGINS
from app.db.database import Base,engine,SessionLocal
from app.db.models import User,Company,Job
from app.core.security import hash_password
from app.api.routes import router
Base.metadata.create_all(bind=engine)
app=FastAPI(title="Emprego Fácil API",version=APP_VERSION)
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS if CORS_ORIGINS!=["*"] else ["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(router)
@app.on_event("startup")
def seed():
    db=SessionLocal()
    if not db.query(User).filter(User.email=="admin@empregofacil.local").first():
        db.add(User(name="Administrador",email="admin@empregofacil.local",password=hash_password("TroqueEstaSenha!123"),role="admin"));db.commit()
    if db.query(Job).count()==0:
        u=User(name="Empresa Demo",email="empresa@demo.com",password=hash_password("123456"),role="company",city="João Pessoa");db.add(u);db.commit();db.refresh(u)
        c=Company(user_id=u.id,name="Empresa Demo",city="João Pessoa",verified=True);db.add(c);db.commit();db.refresh(c)
        db.add_all([
          Job(company_id=c.id,title="Comprador",company="Empresa Demo",city="João Pessoa",salary_min=4500,salary_max=6000,modality="Presencial",contract="CLT",level="Pleno",description="Compras, negociação e fornecedores.",requirements="Compras; negociação; fornecedores; Excel"),
          Job(company_id=c.id,title="Analista de Compras",company="Empresa Demo",city="João Pessoa",salary_min=3500,salary_max=5000,modality="Híbrido",contract="CLT",level="Júnior/Pleno",description="Rotinas de compras e suprimentos.",requirements="Compras; Excel; ERP")]);db.commit()
    db.close()
