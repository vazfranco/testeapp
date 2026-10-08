from fastapi import APIRouter,Depends,HTTPException,UploadFile,File
from fastapi.responses import Response
from pydantic import BaseModel,EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import or_
from io import BytesIO
from reportlab.pdfgen import canvas
from app.db.database import get_db
from app.db.models import *
from app.core.security import hash_password,verify_password,token
from app.api.deps import current_user,role_required
from app.services.matching import score,distance
from app.services.ai import analyze_resume,compare,cover_letter
from app.core.config import FREE_APPLICATION_LIMIT,PREMIUM_APPLICATION_LIMIT

router=APIRouter(prefix="/api/v1")
class Register(BaseModel): name:str;email:EmailStr;password:str;role:str="candidate";city:str="";phone:str=""
class Login(BaseModel): email:EmailStr;password:str
class Profile(BaseModel): name:str|None=None;city:str|None=None;phone:str|None=None;title:str|None=None;salary:float|None=None;remote:str|None=None
class ResumeIn(BaseModel): summary:str="";skills:str="";experience:str="";education:str=""
class JobIn(BaseModel):
    title:str;company:str;city:str;salary_min:float=0;salary_max:float=0;modality:str="Presencial";contract:str="CLT";level:str="Pleno";description:str="";requirements:str="";lat:float|None=None;lon:float|None=None
class MessageIn(BaseModel): receiver_id:int;body:str
class AlertIn(BaseModel): keyword:str;city:str="";modality:str=""
class PushIn(BaseModel): token:str

def user_dict(u): return {k:getattr(u,k) for k in ["id","name","email","role","city","phone","title","salary","remote","plan"]}

@router.get("/health")
def health(): return {"status":"ok","version":"8.0"}

@router.post("/auth/register")
def register(x:Register,db:Session=Depends(get_db)):
    if x.role not in ("candidate","company"): raise HTTPException(400,"role inválido")
    if db.query(User).filter(User.email==x.email).first(): raise HTTPException(409,"E-mail já cadastrado")
    u=User(name=x.name,email=x.email,password=hash_password(x.password),role=x.role,city=x.city,phone=x.phone)
    db.add(u);db.commit();db.refresh(u)
    if x.role=="company": db.add(Company(user_id=u.id,name=x.name,city=x.city));db.commit()
    return {"token":token(u.id,u.role),"user_id":u.id,"role":u.role,"plan":u.plan}

@router.post("/auth/login")
def login(x:Login,db:Session=Depends(get_db)):
    u=db.query(User).filter(User.email==x.email).first()
    if not u or not verify_password(x.password,u.password): raise HTTPException(401,"Login inválido")
    return {"token":token(u.id,u.role),"user_id":u.id,"role":u.role,"plan":u.plan}

@router.post("/auth/oauth/{provider}")
def oauth(provider:str):
    if provider not in ("google","apple"): raise HTTPException(400,"Provider inválido")
    return {"status":"not_configured","provider":provider}

@router.get("/me")
def me(u=Depends(current_user)): return user_dict(u)

@router.put("/me")
def update_me(x:Profile,u=Depends(current_user),db:Session=Depends(get_db)):
    for k,v in x.model_dump(exclude_none=True).items(): setattr(u,k,v)
    db.commit();return user_dict(u)

@router.post("/push/register")
def push(x:PushIn,u=Depends(current_user),db:Session=Depends(get_db)):
    u.push_token=x.token;db.commit();return {"ok":True,"provider":"FCM-ready"}

@router.get("/jobs")
def jobs(q:str="",city:str="",modality:str="",contract:str="",level:str="",salary_min:float=0,salary_max:float=0,lat:float|None=None,lon:float|None=None,radius_km:float|None=None,db:Session=Depends(get_db)):
    qs=db.query(Job).filter(Job.active==True)
    if q: qs=qs.filter(or_(Job.title.ilike(f"%{q}%"),Job.company.ilike(f"%{q}%"),Job.requirements.ilike(f"%{q}%")))
    if city: qs=qs.filter(Job.city.ilike(f"%{city}%"))
    if modality: qs=qs.filter(Job.modality==modality)
    if contract: qs=qs.filter(Job.contract==contract)
    if level: qs=qs.filter(Job.level.ilike(f"%{level}%"))
    if salary_min: qs=qs.filter(Job.salary_max>=salary_min)
    if salary_max: qs=qs.filter(Job.salary_min<=salary_max)
    out=[]
    for j in qs.order_by(Job.created_at.desc()).limit(100).all():
        d=distance(lat,lon,j.lat,j.lon) if lat is not None and lon is not None else None
        if radius_km is not None and d is not None and d>radius_km: continue
        out.append({"id":j.id,"title":j.title,"company":j.company,"city":j.city,"salary_min":j.salary_min,"salary_max":j.salary_max,"modality":j.modality,"contract":j.contract,"level":j.level,"description":j.description,"requirements":j.requirements,"lat":j.lat,"lon":j.lon,"distance_km":round(d,1) if d is not None else None})
    return out

@router.get("/jobs/{job_id}")
def get_job(job_id:int,db:Session=Depends(get_db)):
    j=db.get(Job,job_id)
    if not j or not j.active: raise HTTPException(404,"Vaga não encontrada")
    return {"id":j.id,"title":j.title,"company":j.company,"city":j.city,"salary_min":j.salary_min,"salary_max":j.salary_max,"modality":j.modality,"contract":j.contract,"level":j.level,"description":j.description,"requirements":j.requirements,"lat":j.lat,"lon":j.lon}

@router.post("/jobs")
def create_job(x:JobIn,u=Depends(role_required("company")),db:Session=Depends(get_db)):
    c=db.query(Company).filter(Company.user_id==u.id).first()
    if not c: raise HTTPException(400,"Empresa não configurada")
    j=Job(company_id=c.id,**x.model_dump());db.add(j);db.commit();db.refresh(j);return {"id":j.id}

@router.get("/recommendations")
def recommendations(u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    r=db.query(Resume).filter(Resume.user_id==u.id).first();out=[]
    for j in db.query(Job).filter(Job.active==True).all():
        s,f=score(u,j,r);out.append({"compatibility":s,"factors":f,"job":{"id":j.id,"title":j.title,"company":j.company,"city":j.city,"modality":j.modality}})
    return sorted(out,key=lambda x:x["compatibility"],reverse=True)[:30]

@router.get("/ai/resume-analysis")
def ai_analysis(u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    r=db.query(Resume).filter(Resume.user_id==u.id).first()
    if not r: raise HTTPException(404,"Currículo não preenchido")
    return analyze_resume(r.summary,r.skills,r.experience,r.education)

@router.post("/ai/compare/{job_id}")
def ai_compare(job_id:int,u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    r=db.query(Resume).filter(Resume.user_id==u.id).first();j=db.get(Job,job_id)
    if not r or not j: raise HTTPException(404,"Dados não encontrados")
    return compare(" ".join([r.summary,r.skills,r.experience,r.education])," ".join([j.title,j.requirements,j.description]))

@router.get("/ai/cover-letter/{job_id}")
def ai_cover(job_id:int,u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    j=db.get(Job,job_id)
    if not j: raise HTTPException(404,"Vaga não encontrada")
    return {"text":cover_letter(u.name,u.title,j.title,j.company)}

@router.post("/jobs/{job_id}/favorite")
def favorite(job_id:int,u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    f=db.query(Favorite).filter(Favorite.user_id==u.id,Favorite.job_id==job_id).first()
    if f: db.delete(f);a="removed"
    else: db.add(Favorite(user_id=u.id,job_id=job_id));a="added"
    db.commit();return {"action":a}

@router.get("/favorites")
def favorites(u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    return [{"id":j.id,"title":j.title,"company":j.company,"city":j.city} for j in db.query(Job).join(Favorite,Favorite.job_id==Job.id).filter(Favorite.user_id==u.id).all()]

@router.post("/jobs/{job_id}/apply")
def apply(job_id:int,u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    limit=PREMIUM_APPLICATION_LIMIT if u.plan=="premium" else FREE_APPLICATION_LIMIT
    if db.query(Application).filter(Application.user_id==u.id).count()>=limit: raise HTTPException(402,"Limite do plano atingido")
    if not db.get(Job,job_id): raise HTTPException(404,"Vaga não encontrada")
    if db.query(Application).filter(Application.user_id==u.id,Application.job_id==job_id).first(): raise HTTPException(409,"Já se candidatou")
    a=Application(user_id=u.id,job_id=job_id);db.add(a);db.flush()
    db.add(Event(application_id=a.id,status="Enviada",note="Candidatura enviada"))
    db.add(Notification(user_id=u.id,title="Candidatura enviada",body="Sua candidatura foi registrada.",kind="application"))
    db.commit();return {"id":a.id,"status":a.status}

@router.get("/applications")
def applications(u=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(Application,Job).join(Job,Job.id==Application.job_id).filter(Application.user_id==u.id).all()
    return [{"id":a.id,"job_id":j.id,"title":j.title,"company":j.company,"status":a.status} for a,j in rows]

@router.get("/applications/{app_id}/timeline")
def timeline(app_id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    a=db.get(Application,app_id)
    if not a or a.user_id!=u.id: raise HTTPException(404,"Candidatura não encontrada")
    return [{"status":e.status,"note":e.note,"created_at":e.created_at} for e in db.query(Event).filter(Event.application_id==app_id).order_by(Event.created_at).all()]

@router.put("/resume")
def save_resume(x:ResumeIn,u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    r=db.query(Resume).filter(Resume.user_id==u.id).first()
    if not r:r=Resume(user_id=u.id);db.add(r)
    for k,v in x.model_dump().items():setattr(r,k,v)
    db.commit();return {"ok":True}

@router.get("/resume")
def get_resume(u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    r=db.query(Resume).filter(Resume.user_id==u.id).first()
    return {"summary":r.summary if r else "","skills":r.skills if r else "","experience":r.experience if r else "","education":r.education if r else "","file_name":r.file_name if r else ""}

@router.post("/resume/upload")
async def upload_resume(file:UploadFile=File(...),u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    if file.content_type not in ("application/pdf","application/msword","application/vnd.openxmlformats-officedocument.wordprocessingml.document"): raise HTTPException(400,"Formato não suportado")
    data=await file.read();r=db.query(Resume).filter(Resume.user_id==u.id).first()
    if not r:r=Resume(user_id=u.id);db.add(r)
    r.file_name=file.filename or "curriculo";r.file_data=data;db.commit();return {"ok":True,"file_name":r.file_name}

@router.get("/resume/pdf")
def resume_pdf(u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    r=db.query(Resume).filter(Resume.user_id==u.id).first();b=BytesIO();c=canvas.Canvas(b);c.setFont("Helvetica-Bold",18);c.drawString(50,800,u.name)
    c.setFont("Helvetica",10);c.drawString(50,782,f"{u.email} | {u.phone} | {u.city}");y=745
    for title,text in [("Resumo",r.summary if r else ""),("Habilidades",r.skills if r else ""),("Experiência",r.experience if r else ""),("Formação",r.education if r else "")]:
        c.setFont("Helvetica-Bold",12);c.drawString(50,y,title);y-=18;c.setFont("Helvetica",9)
        for line in (text or "").splitlines()[:12]:c.drawString(55,y,line[:110]);y-=13
        y-=10
    c.save();return Response(b.getvalue(),media_type="application/pdf",headers={"Content-Disposition":'attachment; filename="curriculo.pdf"'})

@router.post("/alerts")
def alert(x:AlertIn,u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    a=Alert(user_id=u.id,**x.model_dump());db.add(a);db.commit();db.refresh(a);return {"id":a.id}

@router.get("/alerts")
def alerts(u=Depends(role_required("candidate")),db:Session=Depends(get_db)):
    return [{"id":a.id,"keyword":a.keyword,"city":a.city,"modality":a.modality,"active":a.active} for a in db.query(Alert).filter(Alert.user_id==u.id).all()]

@router.post("/messages")
def send_message(x:MessageIn,u=Depends(current_user),db:Session=Depends(get_db)):
    if not db.get(User,x.receiver_id): raise HTTPException(404,"Usuário não encontrado")
    m=Message(sender_id=u.id,receiver_id=x.receiver_id,body=x.body);db.add(m);db.add(Notification(user_id=x.receiver_id,title="Nova mensagem",body="Você recebeu uma nova mensagem.",kind="message"));db.commit();return {"id":m.id}

@router.get("/messages/{other_id}")
def messages(other_id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(Message).filter(or_((Message.sender_id==u.id)&(Message.receiver_id==other_id),(Message.sender_id==other_id)&(Message.receiver_id==u.id))).order_by(Message.created_at).all()
    return [{"id":m.id,"sender_id":m.sender_id,"receiver_id":m.receiver_id,"body":m.body,"created_at":m.created_at} for m in rows]

@router.get("/notifications")
def notifications(u=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":n.id,"title":n.title,"body":n.body,"kind":n.kind,"read":n.read} for n in db.query(Notification).filter(Notification.user_id==u.id).order_by(Notification.created_at.desc()).limit(100).all()]

@router.get("/company/dashboard")
def company_dashboard(u=Depends(role_required("company")),db:Session=Depends(get_db)):
    c=db.query(Company).filter(Company.user_id==u.id).first();jobs=db.query(Job).filter(Job.company_id==c.id).all()
    ids=[j.id for j in jobs];apps=db.query(Application).filter(Application.job_id.in_(ids)).count() if ids else 0
    return {"jobs":len(jobs),"applications":apps,"verified":c.verified}

@router.get("/admin/dashboard")
def admin_dashboard(u=Depends(role_required("admin")),db:Session=Depends(get_db)):
    return {"users":db.query(User).count(),"candidates":db.query(User).filter(User.role=="candidate").count(),"companies":db.query(User).filter(User.role=="company").count(),"jobs":db.query(Job).count(),"applications":db.query(Application).count()}
