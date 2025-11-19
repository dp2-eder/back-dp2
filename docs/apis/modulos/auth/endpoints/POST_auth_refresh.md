# POST /auth/refresh

[⬅ Volver al Módulo](../README.md)

## Descripción

Renueva el access token usando un refresh token válido. Útil cuando el access token ha expirado pero el refresh token aún es válido.

## Endpoint

```
POST /api/v1/auth/refresh
```

## Autenticación

**No requerida** — Este endpoint usa el refresh token en el body, no en el header.

## Request Body

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Campos Requeridos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `refresh_token` | `string` | Refresh token JWT válido (no expirado) |

## Response

### 200 OK - Token Renovado Exitosamente

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMUs3WkNUMFBOSkEySjhFQjgzTkhBMU1LNCIsImVtYWlsIjoidXN1YXJpb0BleGFtcGxlLmNvbSIsInJvbF9pZCI6IjAxSzdaQ1Q4UE5KQTJKOEVCODNOSEExTUs1IiwiZXhwIjoxNzI5NjYwOTkwLCJ0eXBlIjoiYWNjZXNzIn0...",
  "token_type": "bearer"
}
```

### 401 Unauthorized - Refresh Token Inválido

```json
{
  "detail": "Refresh token inválido o expirado"
}
```

### 401 Unauthorized - Usuario Inactivo

```json
{
  "detail": "El usuario está inactivo"
}
```

## Ejemplo de Uso

### cURL

```bash
curl -X POST "https://back-dp2.onrender.com/api/v1/auth/refresh" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### JavaScript (fetch)

```javascript
const refreshToken = localStorage.getItem('refresh_token');

const response = await fetch('https://back-dp2.onrender.com/api/v1/auth/refresh', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    refresh_token: refreshToken
  })
});

if (response.ok) {
  const data = await response.json();
  // Actualizar el access token almacenado
  localStorage.setItem('access_token', data.access_token);
  console.log('Token renovado exitosamente');
} else {
  console.error('Error al renovar token');
}
```

## Notas

- El refresh token expira en **30 días** (configurable).
- Solo se genera un nuevo access token, el refresh token se mantiene.
- Si el refresh token expira, el usuario debe iniciar sesión nuevamente.
- El endpoint verifica que el usuario aún exista y esté activo antes de renovar el token.

## Flujo Recomendado

1. Cliente realiza login → recibe `access_token` y `refresh_token`
2. Cliente usa `access_token` para realizar requests autenticados
3. Cuando `access_token` expira (401), cliente llama a `/auth/refresh` con `refresh_token`
4. Cliente recibe nuevo `access_token` y continúa operando
5. Si `refresh_token` también expira, cliente debe hacer login nuevamente

