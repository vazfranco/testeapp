from fastapi import Depends,Header,HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.core.security import decode
def current_user(authorization:str=Header(default=""),db:Session=Depends(get_db)):
    if not authorization.startswith("Bearer "): raise HTTPException(401,"Token ausente")
    try:
        u=db.get(User,int(decode(authorization.split(" ",1)[1])["sub"]))
        if not u or not u.active: raise HTTPException(401,"Usuário inválido")
        return u
    except Exception: raise HTTPException(401,"Token inválido")
def role_required(role):
    def check(u=Depends(current_user)):
        if u.role!=role: raise HTTPException(403,"Permissão insuficiente")
        return u
    return check
