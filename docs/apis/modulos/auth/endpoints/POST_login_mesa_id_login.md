# POST /login/{mesa_id}/login

[⬅ Volver al Módulo](../README.md) · [⬅ Índice](../../../README.md)

## META

- **Host (variable):**
  - **Prod:** `https://back-dp2.onrender.com`
  - **Local:** `http://127.0.0.1:8000`
- **Base Path (constante):** `/api/v1`
- **Recurso (constante):** `/login/{mesa_id}/login`
- **HTTP Method:** `POST`
- **Autenticación:** Ninguna — Endpoint público
- **Notas:** Login simplificado para usuarios temporales de mesas del restaurante

**URL patrón (componentes separadas):**

```
{HOST}{BASE_PATH}/login/{mesa_id}/login
```

---

## Descripción

Autentica (o crea) un usuario temporal en una mesa específica del restaurante. Este endpoint es diferente al login tradicional con JWT — está diseñado para clientes que escanean el QR de una mesa.

### Flujo de Login

1. **Validación de Mesa**: Verifica que la mesa exista y esté activa
2. **Validación de Email**: El email debe contener 'correo', 'mail' o '@'
3. **Gestión de Usuario**: Crea usuario nuevo o actualiza nombre si ya existe
4. **Gestión de Sesión**: Reutiliza sesión activa existente o crea nueva
5. **Expiración de Sesiones**: Marca sesiones expiradas como `FINALIZADA`

### Sesiones Compartidas

Múltiples usuarios en la misma mesa **comparten la misma sesión**:
- Mismo `token_sesion`
- Mismo `id_sesion_mesa`
- Diferentes `id_usuario`

Esto permite que varios clientes en una mesa puedan hacer pedidos bajo la misma sesión.

### Expiración de Sesiones

Las sesiones tienen una duración configurada (por defecto 120 minutos = 2 horas).
Cuando una sesión expira:
- Se marca automáticamente como `FINALIZADA`
- Se crea una nueva sesión `ACTIVA` para el siguiente login

---

## ENTRADA

### Path Params

| Field | Data Type | Required | Format | Comment |
|-------|-----------|----------|--------|---------|
| `mesa_id` | string | YES | ULID | ID único de la mesa |

### Headers

| Field | Data Type | Required | Format | Comment |
|-------|-----------|----------|--------|---------|
| `Content-Type` | string | YES | `application/json` | Tipo de contenido |
| `accept` | string | YES | `application/json` | Tipo de respuesta |

### BODY

```json
{
  "email": "juan@correo.com",
  "nombre": "Juan Pérez"
}
```

**DICTIONARY (BODY)**

| Field | Data Type | Required | Format | Comment |
|-------|-----------|----------|--------|---------|
| `email` | string | YES | 1-255 chars | Debe contener 'correo', 'mail' o '@' |
| `nombre` | string | YES | 1-255 chars | Nombre visible del usuario |

---

## SALIDA (200 OK — Login Exitoso)

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

**DICTIONARY (OUTPUT)**

| Field | Data Type | Format | Comment |
|-------|-----------|--------|---------|
| `status` | integer | 200 | Código HTTP |
| `code` | string | "SUCCESS" | Código de éxito |
| `id_usuario` | string | ULID | ID único del usuario |
| `id_sesion_mesa` | string | ULID | ID de la sesión (compartido entre usuarios de la mesa) |
| `token_sesion` | string | ULID | Token para autenticar pedidos (compartido) |
| `message` | string | - | Mensaje descriptivo |
| `fecha_expiracion` | string | ISO 8601 datetime | Fecha y hora de expiración de la sesión |

---

## ERRORES (4xx/5xx)

### 404 Not Found — Mesa No Existe

```json
{
  "detail": {
    "message": "No se encontró la mesa con ID '01HXXX...'",
    "code": "MESA_NOT_FOUND"
  }
}
```

### 404 Not Found — Mesa Inactiva

```json
{
  "detail": {
    "message": "La mesa '5' no está activa",
    "code": "MESA_INACTIVE"
  }
}
```

### 422 Unprocessable Entity — Email Inválido

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "Value error, El email debe contener 'correo', 'mail' o '@' en su formato",
      "input": "texto_invalido"
    }
  ]
}
```

### 500 Internal Server Error

```json
{
  "detail": "Error procesando login"
}
```

**Tabla de Errores**

| HTTP | Code | Title / Message | Comment |
|------|------|-----------------|---------|
| 404 | `MESA_NOT_FOUND` | Mesa no existe | El `mesa_id` no existe en BD |
| 404 | `MESA_INACTIVE` | Mesa inactiva | La mesa existe pero `activa=false` |
| 422 | `VALIDATION_ERROR` | Email inválido | No contiene 'correo', 'mail' o '@' |
| 500 | `INTERNAL_ERROR` | Error interno | Error inesperado del servidor |

---

## Ejemplos de Uso

### cURL

```bash
# Login exitoso
curl -X POST "https://back-dp2.onrender.com/api/v1/login/01HABC123456789DEF/login" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan@correo.com",
    "nombre": "Juan Pérez"
  }'
```

### JavaScript (fetch)

```javascript
const mesaId = '01HABC123456789DEF';

const response = await fetch(`https://back-dp2.onrender.com/api/v1/login/${mesaId}/login`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'juan@correo.com',
    nombre: 'Juan Pérez'
  })
});

if (response.ok) {
  const data = await response.json();
  console.log('Token de sesión:', data.token_sesion);
  console.log('ID de usuario:', data.id_usuario);
  console.log('Expira:', data.fecha_expiracion);
} else if (response.status === 404) {
  const error = await response.json();
  if (error.detail.code === 'MESA_NOT_FOUND') {
    console.error('Mesa no existe');
  } else if (error.detail.code === 'MESA_INACTIVE') {
    console.error('Mesa inactiva');
  }
}
```

### Python (requests)

```python
import requests

mesa_id = "01HABC123456789DEF"
response = requests.post(
    f'https://back-dp2.onrender.com/api/v1/login/{mesa_id}/login',
    json={
        'email': 'juan@correo.com',
        'nombre': 'Juan Pérez'
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Token: {data['token_sesion']}")
    print(f"Usuario ID: {data['id_usuario']}")
elif response.status_code == 404:
    error = response.json()
    print(f"Error: {error['detail']['message']}")
```

---

## Notas Importantes

1. **Token de Sesión**: El `token_sesion` debe usarse para autenticar pedidos posteriores.

2. **Sesiones Compartidas**: Varios usuarios en la misma mesa reciben el mismo `token_sesion` e `id_sesion_mesa`.

3. **Expiración Automática**: Las sesiones expiran después de 2 horas por defecto. Sesiones expiradas se marcan como `FINALIZADA` automáticamente.

4. **Validación de Email**: Diseñado para emails simples o identificadores que contengan 'correo' o 'mail'.

5. **Idempotencia**: Llamar múltiples veces con el mismo usuario reutiliza la sesión existente (si está activa).

---

## Diagrama de Flujo

```
┌─────────────────┐
│  POST /login/   │
│  {mesa_id}/login│
└────────┬────────┘
         │
         ▼
┌─────────────────┐     No      ┌─────────────────┐
│  ¿Mesa existe?  │────────────▶│   404 Error     │
└────────┬────────┘             │ MESA_NOT_FOUND  │
         │ Sí                   └─────────────────┘
         ▼
┌─────────────────┐     No      ┌─────────────────┐
│  ¿Mesa activa?  │────────────▶│   404 Error     │
└────────┬────────┘             │ MESA_INACTIVE   │
         │ Sí                   └─────────────────┘
         ▼
┌─────────────────┐     No      ┌─────────────────┐
│¿Email válido?   │────────────▶│   422 Error     │
└────────┬────────┘             │ VALIDATION_ERROR│
         │ Sí                   └─────────────────┘
         ▼
┌─────────────────┐
│ ¿Usuario existe?│
└────────┬────────┘
    Sí   │   No
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│Actualizar│ │Crear  │
│nombre   │ │usuario│
└───┬───┘ └───┬───┘
    └────┬────┘
         ▼
┌─────────────────┐
│¿Sesión activa   │
│para esta mesa?  │
└────────┬────────┘
    Sí   │   No
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌─────────────────┐
│Reutilizar│ │¿Sesión expirada?│
│sesión   │ └────────┬────────┘
└───┬───┘      Sí   │   No
    │          ▼    ▼
    │     ┌───────┐ ┌───────┐
    │     │Finalizar│ │Crear  │
    │     │expirada │ │nueva  │
    │     └───┬───┘ └───┬───┘
    │         └────┬────┘
    └──────────────┼──────────────┐
                   ▼              │
              ┌───────┐           │
              │Crear  │◀──────────┘
              │nueva  │
              └───┬───┘
                  ▼
         ┌─────────────────┐
         │   200 SUCCESS   │
         │ LoginResponse   │
         └─────────────────┘
```

---

## Cambios Recientes

| Fecha | Versión | Descripción |
|-------|---------|-------------|
| 2025-11-26 | 1.1.0 | Añadida validación de mesa antes de crear usuario |
| 2025-11-26 | 1.1.0 | Añadido manejo de sesiones expiradas (marca como FINALIZADA) |
| 2025-11-26 | 1.1.0 | Nuevos códigos de error: MESA_NOT_FOUND, MESA_INACTIVE |
