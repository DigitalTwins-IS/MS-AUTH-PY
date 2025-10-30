# MS-AUTH-PY

Microservicio de autenticación y autorización para el sistema Digital Twins.

## 🚀 Quick Start

### Local Development
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp env.example .env

# Ejecutar servidor
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker
```bash
# Build
docker build -t ms-auth-py .

# Run
docker run -p 8001:8000 --env-file .env ms-auth-py
```

## 📋 Requirements

- Python 3.11+
- PostgreSQL con PostGIS
- FastAPI, SQLAlchemy, JWT

## 🔧 Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | 1440 |
| `SERVICE_PORT` | Service port | 8000 |

## 📡 Endpoints

- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/register` - User registration
- `GET /health` - Health check
- `GET /docs` - API documentation

## 🧪 Testing

```bash
pytest tests/ -v
```

## 🔒 Security

- JWT token-based authentication
- Password hashing with bcrypt
- CORS enabled for frontend integration
