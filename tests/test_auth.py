"""
Tests para el microservicio MS-AUTH-PY
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.models import Base, get_db, User
from src.utils import get_password_hash

# Base de datos en memoria para tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la dependency get_db para tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Configurar base de datos para cada test"""
    Base.metadata.create_all(bind=engine)
    
    # Crear usuario de prueba
    db = TestingSessionLocal()
    test_user = User(
        name="Test User",
        email="test@test.com",
        password_hash=get_password_hash("testpass123"),
        role="admin",
        is_active=True
    )
    db.add(test_user)
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)


class TestAuth:
    """Tests de autenticación"""
    
    def test_health_check(self):
        """Test del health check"""
        response = client.get("/api/v1/auth/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "service" in data
        assert "version" in data
    
    def test_login_success(self):
        """Test de login exitoso"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@test.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "test@test.com"
    
    def test_login_wrong_password(self):
        """Test de login con contraseña incorrecta"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@test.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_login_user_not_found(self):
        """Test de login con usuario inexistente"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "notfound@test.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 401
    
    def test_get_me_without_token(self):
        """Test de /me sin token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_get_me_with_token(self):
        """Test de /me con token válido"""
        # Primero hacer login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@test.com",
                "password": "testpass123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Usar el token para obtener /me
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@test.com"
        assert data["role"] == "admin"
    
    def test_logout(self):
        """Test de logout"""
        # Primero hacer login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@test.com",
                "password": "testpass123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Hacer logout
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_register_new_user(self):
        """Test de registro de nuevo usuario"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "New User",
                "email": "newuser@test.com",
                "password": "newpass123",
                "role": "admin"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert "password" not in data  # No debe devolver la contraseña
    
    def test_register_duplicate_email(self):
        """Test de registro con email duplicado"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Duplicate User",
                "email": "test@test.com",  # Email que ya existe
                "password": "password123",
                "role": "admin"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_root_redirect(self):
        """Test de redirección de raíz"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"


class TestSecurity:
    """Tests de seguridad"""
    
    def test_password_hashing(self):
        """Test de que las contraseñas se hashean correctamente"""
        from src.utils import get_password_hash, verify_password
        
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # El hash debe ser diferente de la contraseña original
        assert hashed != password
        
        # Debe poder verificar correctamente
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_jwt_token_structure(self):
        """Test de estructura del token JWT"""
        from src.utils import create_access_token, decode_token
        
        data = {"sub": "test@test.com", "role": "admin"}
        token = create_access_token(data)
        
        # Token debe ser un string
        assert isinstance(token, str)
        
        # Debe poder decodificar el token
        decoded = decode_token(token)
        assert decoded.email == "test@test.com"
        assert decoded.role == "admin"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

