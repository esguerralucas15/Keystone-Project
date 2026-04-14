from fastapi import FastAPI
from app.routes import user_route
from app.routes import chatbot_route
from app.routes import simulator_route
from app.database.database import engine, Base
from app.models.user_model import User
from app.models.profile_model import UserProfile
from app.models.conversation_model import ConversationMessage
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)   

Base.metadata.create_all(bind=engine)

app.include_router(user_route.router, prefix="/users")
app.include_router(chatbot_route.router, prefix="/chatbot")
app.include_router(simulator_route.router, prefix="/simulator")

@app.get("/api")
def root():
    return {"message": "EquiFinance API funcionando 🚀"}

@app.get("/", response_class=HTMLResponse)
def serve_home():
    with open("frontend/index.html", "r", encoding="utf-8") as file:
        return file.read()
    

@app.get("/chat", response_class=HTMLResponse)
def serve_chat():
    with open("frontend/chatbot.html", "r", encoding="utf-8") as file:
        return file.read()
    
