# Módulo: Autenticación

[⬅ Volver al Índice](../../README.md)

## Descripción

Sistema completo de autenticación y gestión de usuarios. Incluye autenticación tradicional con JWT y login simplificado para usuarios temporales de mesas.

## Recursos Base

```
/api/v1/auth     # Autenticación tradicional (JWT)
/api/v1/login    # Login simplificado (sesiones de mesa)
```

## Endpoints Disponibles

### Login Tradicional (JWT)

#### Iniciar Sesión
- **[POST /auth/login](endpoints/POST_auth_login.md)** — Autentica un usuario y genera tokens JWT

#### Registrar Usuario
- **[POST /auth/register](endpoints/POST_auth_register.md)** — Registra un nuevo usuario en el sistema

#### Renovar Token
- **[POST /auth/refresh](endpoints/POST_auth_refresh.md)** — Renueva el access token usando un refresh token válido

#### Usuario Actual
- **[GET /auth/me](endpoints/GET_auth_me.md)** — Obtiene la información del usuario autenticado (requiere autenticación)

---

### Login Simplificado (Sesiones de Mesa)

#### Login de Mesa
- **[POST /login/{mesa_id}/login](endpoints/POST_login_mesa_id_login.md)** — Login simplificado para usuarios temporales de mesas

> ⚠️ **Nota**: Este endpoint es diferente al login tradicional. Está diseñado para clientes que escanean el QR de una mesa y no requiere contraseña.

## Autenticación

### JWT (Endpoints tradicionales)

Este módulo **requiere** autenticación mediante **Bearer Token (JWT)** para el endpoint `/auth/me`. Los endpoints de login, register y refresh son públicos.

#### Header de Autenticación

```http
Authorization: Bearer <jwt_access_token>
```

### Sesiones de Mesa (Login simplificado)

El endpoint `/login/{mesa_id}/login` es **público** y no requiere autenticación previa. Genera un `token_sesion` que se usa para autenticar pedidos.

#### Header de Autenticación para Pedidos

```http
X-Session-Token: <token_sesion>
```

## Schemas Principales

### Login Tradicional (JWT)

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

### Login Simplificado (Sesiones de Mesa)

**LoginResponse (Mesa):**
```json
{
  "status": 200,
  "code": "SUCCESS",
  "id_usuario": "01HABC123456789DEFGHIJK",
  "id_sesion_mesa": "01HDEF123456789GHIJKLM",
  "token_sesion": "01HGHI123456789JKLMNOP",
  "message": "Login exitoso",
  "fecha_expiracion": "2025-11-26T16:30:00"
}
```

**LoginErrorResponse (Mesa):**
```json
{
  "detail": {
    "message": "No se encontró la mesa con ID '01HXXX...'",
    "code": "MESA_NOT_FOUND"
  }
}
```

### Usuario

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

### Login Tradicional (JWT)

- ✅ El **email** del usuario debe ser **único** en el sistema
- ✅ La **contraseña** debe tener al menos **6 caracteres**
- ✅ Los usuarios **inactivos** no pueden iniciar sesión
- ✅ Los **tokens de acceso** expiran en **30 minutos** (configurable)
- ✅ Los **refresh tokens** expiran en **30 días** (configurable)
- ✅ El campo **ultimo_acceso** se actualiza automáticamente en cada login
- ✅ Las contraseñas se almacenan con hash **bcrypt** (nunca en texto plano)

### Login Simplificado (Sesiones de Mesa)

- ✅ La **mesa** debe existir y estar **activa** antes de crear usuario/sesión
- ✅ El **email** debe contener 'correo', 'mail' o '@'
- ✅ Múltiples usuarios en la misma mesa **comparten la sesión**
- ✅ Las sesiones expiran después de **120 minutos** (2 horas) por defecto
- ✅ Las sesiones expiradas se marcan automáticamente como **FINALIZADA**
- ✅ El `token_sesion` se usa para autenticar pedidos posteriores

## Errores Comunes

### Login Tradicional (JWT)

| HTTP | Code | Descripción |
|------|------|-------------|
| 400 | `VALIDATION_ERROR` | Datos de entrada inválidos (email inválido, contraseña muy corta, etc.) |
| 401 | `INVALID_CREDENTIALS` | Email o contraseña incorrectos |
| 401 | `INACTIVE_USER` | Usuario inactivo (no puede iniciar sesión) |
| 401 | `UNAUTHORIZED` | Token inválido o expirado |
| 409 | `USUARIO_CONFLICT` | Ya existe un usuario con ese email |
| 500 | `INTERNAL_ERROR` | Error interno del servidor |

### Login Simplificado (Sesiones de Mesa)

| HTTP | Code | Descripción |
|------|------|-------------|
| 404 | `MESA_NOT_FOUND` | La mesa no existe en la base de datos |
| 404 | `MESA_INACTIVE` | La mesa existe pero está desactivada |
| 422 | `VALIDATION_ERROR` | Email no contiene 'correo', 'mail' o '@' |
| 500 | `INTERNAL_ERROR` | Error interno del servidor |

