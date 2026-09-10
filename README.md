# Language Learning Platform

Language Learning Platform — бул тил үйрөнүүгө арналган backend платформа. Долбоор Duolingo жана Messenger сыяктуу функционалдарды бириктирет.

## Features

- User registration and authentication
- JWT access and refresh tokens
- User roles: User / Admin
- Languages
- Courses
- Lessons
- Exercises
- User progress
- XP system
- Streak system
- Achievements
- Daily challenges
- Leaderboard
- Friends
- Notifications
- Course reviews
- Real-time chat
- WebSocket
- Message reactions
- PostgreSQL database
- Redis
- REST API
- Docker / Docker Compose

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Redis
- WebSocket
- Pydantic
- JWT
- Docker
- Docker Compose

## Architecture

The project uses a modular monolith architecture.

```text
Language-learning-platform/
│
├── backend/
│   ├── api/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   ├── database/
│   └── config.py
│
├── migrations/
│   └── versions/
│
├── main.py
├── alembic.ini
├── .env
├── .gitignore
└── README.md