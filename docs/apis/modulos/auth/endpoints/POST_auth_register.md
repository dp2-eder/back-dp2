# POST /auth/register

[⬅ Volver al Módulo](../README.md)

## Descripción

Registra un nuevo usuario en el sistema. Crea un usuario con email, contraseña, nombre, teléfono y rol asignado.

## Endpoint

```
POST /api/v1/auth/register
```

## Autenticación

**No requerida** — Este es un endpoint público.

## Request Body

```json
{
  "email": "nuevo.usuario@example.com",
  "password": "password123",
  "nombre": "María González",
  "telefono": "987654321",
  "id_rol": "01K7ZCT8PNJA2J8EB83NHA1MK5"
}
```

### Campos Requeridos

| Campo | Tipo | Descripción | Validaciones |
|-------|------|-------------|--------------|
| `email` | `string` | Email del usuario | Debe ser un email válido y único |
| `password` | `string` | Contraseña del usuario | Mínimo 6 caracteres |
| `id_rol` | `string` | ID del rol asignado | Debe existir un rol con este ID |

### Campos Opcionales

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `nombre` | `string` | Nombre completo del usuario (máx. 255 caracteres) |
| `telefono` | `string` | Teléfono del usuario (máx. 20 caracteres) |

## Response

### 201 Created - Registro Exitoso

```json
{
  "usuario": {
    "id": "01K7ZCT8PNJA2J8EB83NHA1MK6",
    "email": "nuevo.usuario@example.com",
    "nombre": "María González",
    "telefono": "987654321",
    "id_rol": "01K7ZCT8PNJA2J8EB83NHA1MK5",
    "activo": true,
    "ultimo_acceso": null,
    "fecha_creacion": "2024-10-23T10:30:45.123456Z",
    "fecha_modificacion": "2024-10-23T10:30:45.123456Z"
  },
  "message": "Usuario registrado exitosamente"
}
```

### 400 Bad Request - Validación Fallida

```json
{
  "detail": "La contraseña debe tener al menos 6 caracteres"
}
```

### 409 Conflict - Email Duplicado

```json
{
  "detail": "Ya existe un usuario con el email 'nuevo.usuario@example.com'"
}
```

## Ejemplo de Uso

### cURL

```bash
curl -X POST "https://back-dp2.onrender.com/api/v1/auth/register" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo.usuario@example.com",
    "password": "password123",
    "nombre": "María González",
    "telefono": "987654321",
    "id_rol": "01K7ZCT8PNJA2J8EB83NHA1MK5"
  }'
```

### JavaScript (fetch)

```javascript
const response = await fetch('https://back-dp2.onrender.com/api/v1/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'nuevo.usuario@example.com',
    password: 'password123',
    nombre: 'María González',
    telefono: '987654321',
    id_rol: '01K7ZCT8PNJA2J8EB83NHA1MK5'
  })
});

const data = await response.json();
console.log('Usuario creado:', data.usuario);
```

## Notas

- La contraseña se almacena con hash bcrypt (nunca en texto plano).
- El usuario se crea con `activo: true` por defecto.
- El email debe ser único en el sistema.
- El `id_rol` debe existir en la tabla de roles.
- Después del registro, el usuario puede iniciar sesión con `/auth/login`.

