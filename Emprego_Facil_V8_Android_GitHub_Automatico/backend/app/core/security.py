import base64,hashlib,hmac,os,jwt
from datetime import datetime,timedelta,timezone
from .config import SECRET_KEY
def hash_password(p):
    s=os.urandom(16); d=hashlib.pbkdf2_hmac("sha256",p.encode(),s,310000)
    return base64.b64encode(s+d).decode()
def verify_password(p,v):
    try:
        r=base64.b64decode(v); d=hashlib.pbkdf2_hmac("sha256",p.encode(),r[:16],310000)
        return hmac.compare_digest(d,r[16:])
    except: return False
def token(uid,role):
    exp=datetime.now(timezone.utc)+timedelta(days=7)
    return jwt.encode({"sub":str(uid),"role":role,"exp":exp},SECRET_KEY,algorithm="HS256")
def decode(t): return jwt.decode(t,SECRET_KEY,algorithms=["HS256"])
