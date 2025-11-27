# Especificación (breve) — GET Nombre del Rol de un Usuario

[⬅ Volver al Módulo](../README.md) · [⬅ Índice](../../../README.md)

## META

- **Host (variable):**
  - **Prod:** `https://back-dp2.onrender.com`
  - **Local:** `http://127.0.0.1:8000`
- **Base Path (constante):** `/api/v1`
- **Recurso (constante):** `/roles/usuario/{usuario_id}/nombre`
- **HTTP Method:** `GET`
- **Autenticación:** (Ninguna)
- **Notas:** En **GET** no enviar body. Usar **path params**.

**URL patrón (componentes separadas):**

```
{HOST}{BASE_PATH}/roles/usuario/{usuario_id}/nombre
```

## DESCRIPCIÓN

Obtiene **únicamente el nombre del rol** asignado a un usuario específico. Este endpoint es útil cuando solo necesitas conocer el rol del usuario sin obtener toda su información completa.

**Caso de uso típico:**
- Verificar rápidamente el rol de un usuario
- Mostrar el rol en interfaces de usuario
- Validaciones rápidas de permisos

## ENTRADA

> **Body:** *(no aplica en GET).*

### Path Params

**DICTIONARY**

| Field | Data Type | Required | Format | Comment |
|-------|-----------|----------|--------|---------|
| `usuario_id` | string | YES | ULID | Identificador único del usuario. |

### Headers

**DICTIONARY**

| Field | Data Type | Required | Format | Comment |
|-------|-----------|----------|--------|---------|
| `accept` | string | YES | `application/json` | Tipo de respuesta. |

## SALIDA (200 OK — ejemplo)

```json
{
  "nombre_rol": "COMENSAL"
}
```

**DICTIONARY (OUTPUT)**

| Field | Data Type | Format | Comment |
|-------|-----------|--------|---------|
| `nombre_rol` | string | | Nombre del rol asignado al usuario (ej: "COMENSAL", "ADMINISTRADOR", "CAMARERO"). |

## ERRORES (4xx/5xx)

### Error 404 - Usuario no encontrado

```json
{
  "detail": "No se encontró el usuario con ID '01K7ZCT8PNJA2J8EB83NHA1MK4'"
}
```

### Error 404 - Usuario sin rol asignado

```json
{
  "detail": "El usuario con ID '01K7ZCT8PNJA2J8EB83NHA1MK4' no tiene un rol asignado"
}
```

### Error 404 - Rol inexistente en base de datos

```json
{
  "detail": "No se encontró el rol con ID '01K7ZCT9QRST3K9FC94OIB2NL5'"
}
```

### Error 500 - Error interno del servidor

```json
{
  "detail": "Error interno del servidor: Database connection error"
}
```

**Tabla de errores:**

| HTTP | Code | Title / Message | Comment |
|------|------|-----------------|---------|
| 404 | `NOT_FOUND` | Usuario no encontrado | El ID de usuario no existe en la base de datos. |
| 404 | `NOT_FOUND` | Usuario sin rol asignado | El usuario existe pero no tiene un rol asociado. |
| 404 | `NOT_FOUND` | Rol inexistente | El usuario tiene un `id_rol` pero ese rol no existe en la BD. |
| 500 | `INTERNAL_ERROR` | Error interno | Error inesperado del servidor. Revisar logs. |

## URLs completas (listas para usar)

### **Producción**

**URL completa:** `https://back-dp2.onrender.com/api/v1/roles/usuario/01K7ZCT8PNJA2J8EB83NHA1MK4/nombre`

**cURL:**

```bash
curl -X GET \
  "https://back-dp2.onrender.com/api/v1/roles/usuario/01K7ZCT8PNJA2J8EB83NHA1MK4/nombre" \
  -H "accept: application/json"
```

**JavaScript (fetch):**

```javascript
const usuarioId = '01K7ZCT8PNJA2J8EB83NHA1MK4';
const response = await fetch(
  `https://back-dp2.onrender.com/api/v1/roles/usuario/${usuarioId}/nombre`,
  {
    method: 'GET',
    headers: {
      'accept': 'application/json'
    }
  }
);

const data = await response.json();
console.log(data.nombre_rol); // "COMENSAL"
```

### **Local**

**URL completa:** `http://127.0.0.1:8000/api/v1/roles/usuario/01K7ZCT8PNJA2J8EB83NHA1MK4/nombre`

**cURL:**

```bash
curl -X GET \
  "http://127.0.0.1:8000/api/v1/roles/usuario/01K7ZCT8PNJA2J8EB83NHA1MK4/nombre" \
  -H "accept: application/json"
```

## EJEMPLO COMPLETO DE USO

### Escenario: Verificar rol de usuario antes de permitir acceso

```javascript
async function verificarAccesoAdministrador(usuarioId) {
  try {
    const response = await fetch(
      `https://back-dp2.onrender.com/api/v1/roles/usuario/${usuarioId}/nombre`,
      {
        method: 'GET',
        headers: {
          'accept': 'application/json'
        }
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        console.error('Usuario no encontrado o sin rol asignado');
        return false;
      }
      throw new Error('Error al verificar rol');
    }

    const data = await response.json();
    
    // Verificar si es administrador
    return data.nombre_rol === 'ADMINISTRADOR';
    
  } catch (error) {
    console.error('Error en verificación de rol:', error);
    return false;
  }
}

// Uso
const usuarioId = '01K7ZCT8PNJA2J8EB83NHA1MK4';
const esAdmin = await verificarAccesoAdministrador(usuarioId);

if (esAdmin) {
  console.log('Acceso concedido al panel de administración');
} else {
  console.log('Acceso denegado');
}
```

## Variables y constantes (resumen)

**Constantes:**
- `BASE_PATH = /api/v1`
- `RECURSO = /roles/usuario/{usuario_id}/nombre`

**Variables:**
- `HOST` = `https://back-dp2.onrender.com` (prod) | `http://127.0.0.1:8000` (local)
- `usuario_id` — ID del usuario cuyo rol se desea consultar

## REGLAS DE NEGOCIO

- ✅ **Respuesta mínima:** Solo retorna el nombre del rol, sin información adicional
- ✅ **Validación de existencia:** Verifica que el usuario exista antes de buscar su rol
- ✅ **Validación de asignación:** Verifica que el usuario tenga un rol asignado
- ✅ **Validación de integridad:** Verifica que el rol asignado exista en la base de datos
- ⚠️ **Sin autenticación:** Actualmente no requiere token de autenticación

## NOTAS TÉCNICAS

- **Performance:** Este endpoint es muy ligero y rápido, ideal para validaciones frecuentes
- **Caché:** Considerar implementar caché si se consulta con mucha frecuencia
- **Alternativa:** Si necesitas más información del usuario, usa `GET /usuarios/{usuario_id}`
