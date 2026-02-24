from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from database import Base



# جدول metrics
class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, nullable=False)
    hostname = Column(String, nullable=False)
    cpu = Column(Float, nullable=False)
    ram = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))


# جدول users
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True , nullable=False)
    password = Column(String , nullable=False)

#جدول Alert
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    agent_id = Column(String)
    hostname = Column(String)
    metric_type = Column(String)
    value = Column(Float)
    severity = Column(String)
    status = Column(String)
    message = Column(String)
    timestamp = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))




#جدول Agent
class Agent(Base):
    __tablename__ = "agents"

    agent_id = Column(String, primary_key=True, index=True)
    hostname = Column(String)
    ip_address = Column(String)
    last_seen = Column(DateTime(timezone=True))
    is_online = Column(Boolean, default=True)