import re
from app.core.config import AI_PROVIDER
def analyze_resume(summary,skills,experience,education):
    text=" ".join([summary,skills,experience,education])
    suggestions=[]
    if len(text)<300: suggestions.append("Aumente o resumo profissional com resultados mensuráveis.")
    if not any(x in text.lower() for x in ["excel","erp","sap"]): suggestions.append("Informe ferramentas relevantes para sua área.")
    if not any(x in text.lower() for x in ["resultado","redução","economia","aumento","melhoria"]): suggestions.append("Inclua resultados, economia, ganhos de prazo ou produtividade.")
    words=set(re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}",text.lower()))
    return {"provider":AI_PROVIDER,"suggestions":suggestions,"keywords":sorted(words)[:30]}
def compare(resume_text,job_text):
    r=set(re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}",resume_text.lower()));j=set(re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}",job_text.lower()))
    common=sorted(r&j);missing=sorted(j-r)
    return {"match_percent":min(99,round(len(common)/max(1,len(j))*100)),"matching_keywords":common[:30],"missing_keywords":missing[:30]}
def cover_letter(name,title,job,company):
    return ("Olá, equipe "+company+",\n\nMeu nome é "+name+" e atuo como "+(title or "profissional da área")+
            ". Tenho interesse na oportunidade de "+job+" e acredito que minha experiência pode contribuir para a empresa.\n\n"
            "Gostaria de participar do processo seletivo e apresentar melhor minha experiência.\n\nAtenciosamente,\n"+name)
