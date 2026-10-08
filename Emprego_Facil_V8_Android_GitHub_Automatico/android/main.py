import requests
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
import json, os
API="http://10.0.2.2:8000/api/v1"; TOKEN=""

def settings_file():
    return os.path.join(App.get_running_app().user_data_dir, "settings.json")

def load_settings():
    global API, TOKEN
    try:
        with open(settings_file(), encoding="utf-8") as f: d=json.load(f)
        API=d.get("api",API); TOKEN=d.get("token","")
    except Exception: pass

def save_settings():
    os.makedirs(os.path.dirname(settings_file()), exist_ok=True)
    with open(settings_file(),"w",encoding="utf-8") as f: json.dump({"api":API,"token":TOKEN},f)
KV='''ScreenManager:
 Login:
 Home:
 Jobs:
 AI:
<Login>:
 name:"login"
 BoxLayout:
  orientation:"vertical";padding:30;spacing:12
  Label:text:"Emprego Fácil V8";font_size:"28sp";bold:True
  TextInput:id:e;hint_text:"E-mail";multiline:False
  TextInput:id:p;hint_text:"Senha";password:True;multiline:False
  Button:text:"Entrar";on_release:root.login(e.text,p.text)
  Label:id:s;text:""
<Home>:
 name:"home"
 BoxLayout:
  orientation:"vertical";padding:20;spacing:10
  Label:text:"Painel";font_size:"25sp"
  Button:text:"🔎 Buscar vagas";on_release:app.root.current="jobs"
  Button:text:"🤖 Analisar currículo";on_release:app.root.current="ai"
  Button:text:"⭐ Recomendações";on_release:root.recommend()
  Button:text:"🔔 Notificações";on_release:root.notifications()
  Label:id:r;text:""
<Jobs>:
 name:"jobs"
 BoxLayout:
  orientation:"vertical";padding:15;spacing:8
  TextInput:id:q;hint_text:"Cargo / palavra-chave";multiline:False
  TextInput:id:c;hint_text:"Cidade";multiline:False
  Button:text:"Buscar";on_release:root.search(q.text,c.text)
  ScrollView:
   Label:id:r;text:"";text_size:self.width,None;size_hint_y:None;height:self.texture_size[1]
  Button:text:"Voltar";on_release:app.root.current="home"
<AI>:
 name:"ai"
 BoxLayout:
  orientation:"vertical";padding:15;spacing:10
  Label:id:r;text:"Análise";text_size:self.width,None
  Button:text:"Executar";on_release:root.run()
  Button:text:"Voltar";on_release:app.root.current="home"
'''
class Login(Screen):
 def login(self,e,p):
  global TOKEN
  try:
   r=requests.post(API+"/auth/login",json={"email":e,"password":p},timeout=10)
   if r.ok:TOKEN=r.json()["token"];save_settings();self.manager.current="home"
   else:self.ids.s.text="Login inválido"
  except:self.ids.s.text="API indisponível"
class Home(Screen):
 def recommend(self):
  try:
   d=requests.get(API+"/recommendations",headers={"Authorization":"Bearer "+TOKEN}).json()
   self.ids.r.text="\n".join([f"{x['job']['title']} — {x['compatibility']}%" for x in d[:8]])
  except:self.ids.r.text="Faça login como candidato."
 def notifications(self):
  try:
   d=requests.get(API+"/notifications",headers={"Authorization":"Bearer "+TOKEN}).json()
   self.ids.r.text="\n".join([x["title"] for x in d[:8]]) or "Sem notificações."
  except:self.ids.r.text="Erro."
class Jobs(Screen):
 def search(self,q,c):
  try:
   d=requests.get(API+"/jobs",params={"q":q,"city":c}).json()
   self.ids.r.text="\n\n".join([f"{x['title']} — {x['company']}\n{x['city']} | {x['modality']} | R$ {x['salary_min']:.0f}–{x['salary_max']:.0f}" for x in d]) or "Nenhuma vaga."
  except:self.ids.r.text="Erro."
class AI(Screen):
 def run(self):
  try:
   d=requests.get(API+"/ai/resume-analysis",headers={"Authorization":"Bearer "+TOKEN}).json()
   self.ids.r.text="\n".join(d.get("suggestions",[])) or "Nenhum alerta básico."
  except:self.ids.r.text="Preencha seu currículo."
class AppV8(App):
 def build(self):
  load_settings()
  return Builder.load_string(KV)
AppV8().run()
