import os
APP_VERSION=os.getenv("APP_VERSION","8.0.0")
SECRET_KEY=os.getenv("SECRET_KEY","dev-change-me")
DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./emprego_v8.db")
CORS_ORIGINS=os.getenv("CORS_ORIGINS","*").split(",")
AI_PROVIDER=os.getenv("AI_PROVIDER","local")
FREE_APPLICATION_LIMIT=int(os.getenv("FREE_APPLICATION_LIMIT","10"))
PREMIUM_APPLICATION_LIMIT=int(os.getenv("PREMIUM_APPLICATION_LIMIT","1000"))
