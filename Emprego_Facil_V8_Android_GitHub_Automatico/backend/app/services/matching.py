import re,math
def terms(s): return set(re.findall(r"[a-zA-ZÀ-ÿ0-9]{3,}",(s or "").lower()))
def score(user,job,resume=None):
    rt=" ".join([resume.skills,resume.experience,resume.education]) if resume else ""
    a=terms((user.title or "")+" "+rt); b=terms((job.title or "")+" "+(job.requirements or "")+" "+(job.description or ""))
    factors={"keywords":round(min(55,len(a&b)/max(1,len(b))*55)),"location":15 if user.city.lower()==job.city.lower() and user.city else 0,
             "modality":10 if user.remote.lower() in job.modality.lower() else 0,
             "salary":10 if user.salary and job.salary_max>=user.salary else 0,
             "title":10 if user.title and user.title.lower() in job.title.lower() else 0}
    return min(99,sum(factors.values())),factors
def distance(a,b,c,d):
    if None in (a,b,c,d): return None
    r=6371;p=math.radians(a);q=math.radians(c)
    x=math.sin(math.radians(c-a)/2)**2+math.cos(p)*math.cos(q)*math.sin(math.radians(d-b)/2)**2
    return r*2*math.atan2(math.sqrt(x),math.sqrt(1-x))
