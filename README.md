# Distributed Monitoring Platform

A distributed system monitoring platform built with:

- FastAPI (Backend API)
- Docker (Containerization)
- Python Agent (System Metrics Collector)
- Flutter (Dashboard UI)
- JWT Authentication

---

## 📌 Overview

This project implements a distributed monitoring architecture:

- Monitoring Agents collect system metrics (CPU, RAM).
- Backend API receives and stores metrics.
- Dashboard visualizes metrics in real-time.
- JWT authentication protects API endpoints.

---

## 🏗️ Architecture

Agent (Python) → Backend (FastAPI + Docker) → Flutter Dashboard

---

## 🚀 Features

- CPU & RAM monitoring
- Agent heartbeat tracking
- Real-time dashboard updates
- JWT Authentication
- Dockerized backend
- RESTful API

---

## 🛠️ Tech Stack

Backend:
- FastAPI
- SQLAlchemy
- SQLite
- Docker

Agent:
- Python
- psutil
- requests

Frontend:
- Flutter
- Syncfusion Charts

Authentication:
- JWT (JSON Web Token)

