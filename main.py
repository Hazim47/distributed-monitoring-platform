from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import threading
import time
from jose import jwt, JWTError

from database import SessionLocal, engine, Base
from models import Metric, User, Agent, Alert
from auth import create_token, verify_password

# =========================
# CONFIG
# =========================
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

app = FastAPI(title="Distributed Monitoring Platform")
Base.metadata.create_all(bind=engine)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DB Dependency
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# JWT Authentication
# =========================
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# =========================
# Background Jobs
# =========================
def cleanup_old_metrics(db: Session):
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    db.query(Metric).filter(Metric.timestamp < cutoff_date).delete()
    db.commit()

def check_offline_agents(db: Session):
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=15)
    agents = db.query(Agent).all()
    for agent in agents:
        agent.is_online = agent.last_seen >= cutoff
    db.commit()

def scheduler():
    while True:
        db = SessionLocal()
        try:
            cleanup_old_metrics(db)
            check_offline_agents(db)
        finally:
            db.close()
        time.sleep(10)

@app.on_event("startup")
def startup():
    thread = threading.Thread(target=scheduler, daemon=True)
    thread.start()

# =========================
# Schemas
# =========================
class MetricsIn(BaseModel):
    agent_id: str
    hostname: str
    cpu: float
    ram: float

class MetricsOut(BaseModel):
    agent_id: str
    hostname: str
    cpu: float
    ram: float
    timestamp: datetime
    class Config:
        from_attributes = True

class LoginIn(BaseModel):
    username: str
    password: str

# =========================
# AUTH
# =========================
@app.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Wrong password")
    token = create_token(user.username)
    return {"access_token": token}

# =========================
# Agent
# =========================
@app.post("/agents/register")
def register_agent(agent_id: str, hostname: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        agent = Agent(agent_id=agent_id, hostname=hostname,
                      last_seen=datetime.now(timezone.utc), is_online=True)
        db.add(agent)
    else:
        agent.last_seen = datetime.now(timezone.utc)
        agent.is_online = True
    db.commit()
    return {"status": "registered"}

@app.get("/agents")
def get_agents(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    agents = db.query(Agent).all()
    return agents

# =========================
# METRICS
# =========================
@app.post("/metrics")
def receive_metrics(data: MetricsIn, db: Session = Depends(get_db)):
    metric = Metric(agent_id=data.agent_id, hostname=data.hostname,
                    cpu=data.cpu, ram=data.ram)
    db.add(metric)
    # Update Agent heartbeat
    agent = db.query(Agent).filter(Agent.agent_id == data.agent_id).first()
    if agent:
        agent.last_seen = datetime.now(timezone.utc)
        agent.is_online = True
    # 🚨 Alerts
    if data.cpu > 80:
        db.add(Alert(agent_id=data.agent_id, hostname=data.hostname,
                     metric_type="CPU", value=data.cpu,
                     severity="critical", status="active",
                     message=f"High CPU usage: {data.cpu}%"))
    if data.ram > 90:
        db.add(Alert(agent_id=data.agent_id, hostname=data.hostname,
                     metric_type="RAM", value=data.ram,
                     severity="critical", status="active",
                     message=f"High RAM usage: {data.ram}%"))
    db.commit()
    return {"status": "saved"}

@app.get("/metrics", response_model=List[MetricsOut])
def get_metrics(limit: int = 50, db: Session = Depends(get_db),
                user: str = Depends(get_current_user)):
    return db.query(Metric).order_by(Metric.timestamp.desc()).limit(limit).all()

@app.get("/metrics/latest", response_model=List[MetricsOut])
def get_latest_metrics(limit: int = 10, db: Session = Depends(get_db),
                       user: str = Depends(get_current_user)):
    return db.query(Metric).order_by(Metric.timestamp.desc()).limit(limit).all()

# =========================
# Alerts
# =========================
@app.get("/alerts")
def get_alerts(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return db.query(Alert).order_by(Alert.timestamp.desc()).limit(50).all()

@app.patch("/alerts/{alert_id}/ack")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "acknowledged"
    db.commit()
    return {"status": "acknowledged"}