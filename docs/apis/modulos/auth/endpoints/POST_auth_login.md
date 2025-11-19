# POST /auth/login

[⬅ Volver al Módulo](../README.md)

## Descripción

Autentica un usuario con email y contraseña, devuelve tokens JWT (access token y refresh token) junto con la información del usuario.

## Endpoint

```
POST /api/v1/auth/login
```

## Autenticación

**No requerida** — Este es un endpoint público.

## Request Body

```json
{
  "email": "usuario@example.com",
  "password": "password123"
}
```

### Campos Requeridos

| Campo | Tipo | Descripción | Validaciones |
|-------|------|-------------|--------------|
| `email` | `string` | Email del usuario | Debe ser un email válido |
| `password` | `string` | Contraseña del usuario | Mínimo 1 carácter |

## Response

### 200 OK - Login Exitoso

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMUs3WkNUMFBOSkEySjhFQjgzTkhBMU1LNCIsImVtYWlsIjoidXN1YXJpb0BleGFtcGxlLmNvbSIsInJvbF9pZCI6IjAxSzdaQ1Q4UE5KQTJKOEVCODNOSEExTUs1IiwiZXhwIjoxNzI5NjYwOTkwLCJ0eXBlIjoiYWNjZXNzIn0...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMUs3WkNUMFBOSkEySjhFQjgzTkhBMU1LNCIsImVtYWlsIjoidXN1YXJpb0BleGFtcGxlLmNvbSIsInJvbF9pZCI6IjAxSzdaQ1Q4UE5KQTJKOEVCODNOSEExTUs1IiwiZXhwIjoxNzMwMjY1NzkwLCJ0eXBlIjoicmVmcmVzaCJ9...",
  "token_type": "bearer",
  "usuario": {
    "id": "01K7ZCT8PNJA2J8EB83NHA1MK4",
    "email": "usuario@example.com",
    "nombre": "Juan Pérez",
    "telefono": "123456789",
    "id_rol": "01K7ZCT8PNJA2J8EB83NHA1MK5",
    "activo": true,
    "ultimo_acceso": "2024-10-23T10:30:45.123456Z",
    "fecha_creacion": "2024-10-23T05:16:30.123456Z",
    "fecha_modificacion": "2024-10-23T10:30:45.123456Z"
  }
}
```

### 401 Unauthorized - Credenciales Inválidas

```json
{
  "detail": "Email o contraseña incorrectos"
}
```

### 401 Unauthorized - Usuario Inactivo

```json
{
  "detail": "El usuario está inactivo. Contacte al administrador."
}
```

## Ejemplo de Uso

### cURL

```bash
curl -X POST "https://back-dp2.onrender.com/api/v1/auth/login" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "password123"
  }'
```

### JavaScript (fetch)

```javascript
const response = await fetch('https://back-dp2.onrender.com/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'usuario@example.com',
    password: 'password123'
  })
});

const data = await response.json();
console.log('Access Token:', data.access_token);
console.log('User:', data.usuario);
```

### Python (requests)

```python
import requests

response = requests.post(
    'https://back-dp2.onrender.com/api/v1/auth/login',
    json={
        'email': 'usuario@example.com',
        'password': 'password123'
    }
)

data = response.json()
access_token = data['access_token']
print(f'Access Token: {access_token}')
```

## Notas

- El campo `ultimo_acceso` se actualiza automáticamente al realizar el login exitoso.
- Guarda el `refresh_token` de forma segura para renovar el access token cuando expire.
- El `access_token` debe incluirse en el header `Authorization: Bearer <token>` para acceder a endpoints protegidos.
- Los tokens contienen información del usuario (`sub`: usuario ID, `email`, `rol_id`).

