# Módulo: Autenticación

[⬅ Volver al Índice](../../README.md)

## Descripción

Sistema completo de autenticación y gestión de usuarios. Permite registro, inicio de sesión, renovación de tokens y consulta del usuario actual.

## Recurso Base

```
/api/v1/auth
```

## Endpoints Disponibles

### Iniciar Sesión
- **[POST /auth/login](endpoints/POST_auth_login.md)** — Autentica un usuario y genera tokens JWT

### Registrar Usuario
- **[POST /auth/register](endpoints/POST_auth_register.md)** — Registra un nuevo usuario en el sistema

### Renovar Token
- **[POST /auth/refresh](endpoints/POST_auth_refresh.md)** — Renueva el access token usando un refresh token válido

### Usuario Actual
- **[GET /auth/me](endpoints/GET_auth_me.md)** — Obtiene la información del usuario autenticado (requiere autenticación)

## Autenticación

Este módulo **requiere** autenticación mediante **Bearer Token (JWT)** para el endpoint `/auth/me`. Los endpoints de login, register y refresh son públicos.

### Header de Autenticación

```http
Authorization: Bearer <jwt_access_token>
```

## Schemas Principales

**LoginResponse:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "usuario": {
    "id": "01K7ZCT8PNJA2J8EB83NHA1MK4",
    "email": "usuario@example.com",
    "nombre": "Juan Pérez",
    "telefono": "123456789",
    "activo": true,
    "id_rol": "01K7ZCT8PNJA2J8EB83NHA1MK5",
    "ultimo_acceso": "2024-10-23T05:16:30.123456Z",
    "fecha_creacion": "2024-10-23T05:16:30.123456Z",
    "fecha_modificacion": "2024-10-23T05:16:30.123456Z"
  }
}
```

**UsuarioResponse:**
```json
{
  "id": "01K7ZCT8PNJA2J8EB83NHA1MK4",
  "email": "usuario@example.com",
  "nombre": "Juan Pérez",
  "telefono": "123456789",
  "id_rol": "01K7ZCT8PNJA2J8EB83NHA1MK5",
  "activo": true,
  "ultimo_acceso": "2024-10-23T05:16:30.123456Z",
  "fecha_creacion": "2024-10-23T05:16:30.123456Z",
  "fecha_modificacion": "2024-10-23T05:16:30.123456Z"
}
```

## Reglas de Negocio

- ✅ El **email** del usuario debe ser **único** en el sistema
- ✅ La **contraseña** debe tener al menos **6 caracteres**
- ✅ Los usuarios **inactivos** no pueden iniciar sesión
- ✅ Los **tokens de acceso** expiran en **30 minutos** (configurable)
- ✅ Los **refresh tokens** expiran en **30 días** (configurable)
- ✅ El campo **ultimo_acceso** se actualiza automáticamente en cada login
- ✅ Las contraseñas se almacenan con hash **bcrypt** (nunca en texto plano)

## Errores Comunes

| HTTP | Code | Descripción |
|------|------|-------------|
| 400 | `VALIDATION_ERROR` | Datos de entrada inválidos (email inválido, contraseña muy corta, etc.) |
| 401 | `INVALID_CREDENTIALS` | Email o contraseña incorrectos |
| 401 | `INACTIVE_USER` | Usuario inactivo (no puede iniciar sesión) |
| 401 | `UNAUTHORIZED` | Token inválido o expirado |
| 409 | `USUARIO_CONFLICT` | Ya existe un usuario con ese email |
| 500 | `INTERNAL_ERROR` | Error interno del servidor |

