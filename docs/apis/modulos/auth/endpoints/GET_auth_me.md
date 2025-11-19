# GET /auth/me

[⬅ Volver al Módulo](../README.md)

## Descripción

Obtiene la información del usuario autenticado usando el token JWT del header Authorization. Este endpoint requiere autenticación.

## Endpoint

```
GET /api/v1/auth/me
```

## Autenticación

**Requerida** — Requiere un access token válido en el header Authorization.

### Header Requerido

```http
Authorization: Bearer <access_token>
```

## Response

### 200 OK - Usuario Encontrado

```json
{
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
```

### 401 Unauthorized - Token Inválido o Ausente

```json
{
  "detail": "Token inválido o expirado"
}
```

```http
WWW-Authenticate: Bearer
```

### 401 Unauthorized - Usuario Inactivo

```json
{
  "detail": "Usuario inactivo"
}
```

## Ejemplo de Uso

### cURL

```bash
curl -X GET "https://back-dp2.onrender.com/api/v1/auth/me" \
  -H "accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### JavaScript (fetch)

```javascript
const accessToken = localStorage.getItem('access_token');

const response = await fetch('https://back-dp2.onrender.com/api/v1/auth/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

if (response.ok) {
  const usuario = await response.json();
  console.log('Usuario actual:', usuario);
} else if (response.status === 401) {
  // Token expirado, intentar renovar
  await refreshAccessToken();
}
```

### Python (requests)

```python
import requests

access_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

response = requests.get(
    'https://back-dp2.onrender.com/api/v1/auth/me',
    headers={
        'Authorization': f'Bearer {access_token}'
    }
)

if response.status_code == 200:
    usuario = response.json()
    print(f'Usuario: {usuario["nombre"]} ({usuario["email"]})')
elif response.status_code == 401:
    print('Token expirado, renovar token')
```

## Notas

- El token se extrae del header `Authorization` con el formato `Bearer <token>`.
- El endpoint verifica que el token sea válido y no esté expirado.
- Verifica que el usuario exista y esté activo.
- Útil para validar el estado de autenticación del cliente y obtener información del usuario sin hacer login nuevamente.

