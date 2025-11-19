# Flujo Completo de Sesiones de Mesa - Sistema de Restaurante

## Índice
1. [Visión General](#visión-general)
2. [Conceptos Clave](#conceptos-clave)
3. [Estados de la Sesión](#estados-de-la-sesión)
4. [Flujo Completo Paso a Paso](#flujo-completo-paso-a-paso)
5. [Escenarios Específicos](#escenarios-específicos)
6. [Validaciones y Reglas de Negocio](#validaciones-y-reglas-de-negocio)
7. [Modelos de Datos](#modelos-de-datos)
8. [Endpoints API](#endpoints-api)

---

## Visión General

El sistema de sesiones de mesa permite que **múltiples usuarios compartan una misma sesión** en una mesa del restaurante. Esto facilita que un grupo de personas pueda hacer pedidos de forma colaborativa usando un **token compartido**.

### Características Principales:
- ✅ Una sesión de mesa puede tener **múltiples usuarios**
- ✅ Todos los usuarios de una mesa **comparten el mismo token**
- ✅ Solo puede existir **una sesión activa por mesa** a la vez
- ✅ Las sesiones tienen una **duración configurable** (por defecto 120 minutos)
- ✅ Las sesiones pueden cerrarse **manualmente o por expiración automática**
- ✅ El historial de pedidos está vinculado a la sesión

---

## Conceptos Clave

### 1. Sesión de Mesa (`SesionMesaModel`)
Es la entidad central que representa una sesión temporal en una mesa del restaurante.

**Atributos principales:**
- `id`: Identificador único (ULID)
- `id_mesa`: Mesa donde se realiza la sesión
- `id_usuario_creador`: Usuario que creó la sesión (primer usuario en llegar)
- `token_sesion`: Token único compartido por todos los usuarios (ULID de 26 caracteres)
- `estado`: Estado actual (ACTIVA, INACTIVA, CERRADA, FINALIZADA)
- `fecha_inicio`: Momento en que se creó la sesión
- `fecha_fin`: Momento en que se cerró (opcional)
- `duracion_minutos`: Duración configurada (por defecto 120 minutos)

### 2. Relación Usuario-Sesión (`UsuarioSesionMesaModel`)
Tabla intermedia que vincula usuarios con sesiones de mesa (relación many-to-many).

**Atributos principales:**
- `id`: Identificador único (ULID)
- `id_usuario`: Usuario asociado a la sesión
- `id_sesion_mesa`: Sesión de mesa asociada
- `fecha_ingreso`: Momento en que el usuario se unió a la sesión

### 3. Token de Sesión
- Es un **ULID único de 26 caracteres** generado al crear la sesión
- Se **comparte entre todos los usuarios** de la mesa
- Se utiliza para:
  - Crear pedidos sin necesidad de autenticación tradicional
  - Consultar el historial de pedidos de la mesa
  - Cerrar la sesión

---

## Estados de la Sesión

### Estados Disponibles (`EstadoSesionMesa`)

#### 1. **ACTIVA** (`"activa"`)
- La sesión está operativa
- Se pueden crear pedidos
- Los usuarios pueden unirse a la sesión
- Es el estado por defecto al crear una sesión

#### 2. **INACTIVA** (`"inactiva"`)
- La sesión existe pero está temporalmente deshabilitada
- NO se pueden crear pedidos
- Estado temporal para casos especiales

#### 3. **CERRADA** (`"cerrada"`)
- La sesión fue cerrada manualmente (por un usuario o administrador)
- NO se pueden crear más pedidos
- El historial retorna lista vacía con mensaje informativo
- Estado definitivo

#### 4. **FINALIZADA** (`"finalizada"`)
- La sesión fue finalizada por el sistema (expiración automática)
- NO se pueden crear más pedidos
- Similar a CERRADA pero por tiempo
- Estado definitivo

---

## Flujo Completo Paso a Paso

### FASE 1: Llegada del Primer Usuario a la Mesa

#### Paso 1.1: Usuario escanea QR de la mesa
El QR contiene el `id_mesa` (ULID de la mesa física).

#### Paso 1.2: Usuario ingresa sus datos
El frontend presenta un formulario simple:
- **Email**: Puede ser cualquier string que contenga "correo", "mail" o "@"
- **Nombre**: Nombre del usuario

#### Paso 1.3: Sistema valida el email
```
Validación de formato de email:
- Debe contener "correo", "mail" o "@"
- Si no cumple: ERROR "El email debe contener 'correo', 'mail' o '@' en su formato"
```

#### Paso 1.4: Sistema busca si el usuario ya existe
```
Query: SELECT * FROM usuarios WHERE email = ?
```

**Caso A: Usuario NO existe**
1. Sistema crea nuevo usuario:
   ```
   UsuarioModel(
     id: ULID generado,
     email: email proporcionado,
     nombre: nombre proporcionado,
     ultimo_acceso: fecha actual
   )
   ```

**Caso B: Usuario existe**
1. Sistema verifica si el nombre coincide:
   - **Si el nombre es diferente**: Actualiza el nombre y `ultimo_acceso`
   - **Si el nombre coincide**: Solo actualiza `ultimo_acceso`

#### Paso 1.5: Sistema busca sesión activa para la mesa
```
Query:
  SELECT * FROM sesiones_mesas
  WHERE id_mesa = ?
    AND estado = 'ACTIVA'
  ORDER BY fecha_inicio DESC
  LIMIT 1
```

**Resultado esperado en este caso**: NO existe sesión activa (es el primer usuario)

#### Paso 1.6: Sistema crea nueva sesión de mesa
```
SesionMesaModel(
  id: ULID generado,
  id_mesa: id_mesa del QR,
  id_usuario_creador: id del usuario creado/encontrado,
  token_sesion: ULID generado (26 caracteres),
  estado: ACTIVA,
  fecha_inicio: fecha actual,
  fecha_fin: NULL,
  duracion_minutos: 120
)
```

#### Paso 1.7: Sistema asocia el usuario a la sesión
```
UsuarioSesionMesaModel(
  id: ULID generado,
  id_usuario: id del usuario,
  id_sesion_mesa: id de la sesión creada,
  fecha_ingreso: fecha actual
)
```

#### Paso 1.8: Sistema calcula fecha de expiración
```
fecha_expiracion = fecha_inicio + duracion_minutos
Ejemplo: 2025-11-18 01:00:00 + 120 minutos = 2025-11-18 03:00:00
```

#### Paso 1.9: Sistema retorna respuesta al frontend
```json
{
  "status": 200,
  "code": "SUCCESS",
  "id_usuario": "01KAANBJ4DG4A6H5TKBDEBKW72",
  "id_sesion_mesa": "01KAASS2HQGS37Q42YQ6XXJZWR",
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
  "message": "Login exitoso",
  "fecha_expiracion": "2025-11-18T03:00:00"
}
```

#### Paso 1.10: Frontend almacena el token
El frontend guarda:
- `token_sesion` (para hacer pedidos y consultar historial)
- `id_sesion_mesa` (opcional, para referencia)
- `id_usuario` (opcional, para referencia)

---

### FASE 2: Llegada de Usuarios Adicionales a la Mesa

#### Paso 2.1: Segundo/Tercer/Cuarto usuario escanea el mismo QR

#### Paso 2.2: Usuario ingresa sus datos
Email y nombre (igual que el primer usuario).

#### Paso 2.3: Sistema valida email y busca/crea usuario
(Mismo proceso que Fase 1, Pasos 1.3 y 1.4)

#### Paso 2.4: Sistema busca sesión activa para la mesa
```
Query:
  SELECT * FROM sesiones_mesas
  WHERE id_mesa = ?
    AND estado = 'ACTIVA'
  ORDER BY fecha_inicio DESC
  LIMIT 1
```

**Resultado esperado en este caso**: SÍ existe sesión activa (la creada por el primer usuario)

#### Paso 2.5: Sistema verifica si la sesión está expirada
```
Verificación:
  datetime.now() > (fecha_inicio + duracion_minutos)
```

**Caso A: Sesión NO expirada**
- Continúa al Paso 2.6

**Caso B: Sesión expirada**
1. Sistema finaliza la sesión expirada:
   ```
   UPDATE sesiones_mesas
   SET estado = 'FINALIZADA', fecha_fin = NOW()
   WHERE id = ?
   ```
2. Sistema crea una NUEVA sesión (repite Paso 1.6)
3. Asocia al usuario a la nueva sesión (repite Paso 1.7)
4. Retorna respuesta con el nuevo token

#### Paso 2.6: Sistema verifica si el usuario ya está en la sesión
```
Query:
  SELECT * FROM usuarios_sesiones_mesas
  WHERE id_usuario = ? AND id_sesion_mesa = ?
```

**Caso A: Usuario NO está en la sesión**
1. Sistema asocia al usuario a la sesión existente:
   ```
   UsuarioSesionMesaModel(
     id: ULID generado,
     id_usuario: id del usuario,
     id_sesion_mesa: id de la sesión existente,
     fecha_ingreso: fecha actual
   )
   ```

**Caso B: Usuario YA está en la sesión**
1. Sistema NO hace nada (reutiliza la asociación existente)

#### Paso 2.7: Sistema retorna respuesta con el MISMO token
```json
{
  "status": 200,
  "code": "SUCCESS",
  "id_usuario": "01KAANBJ4XXXXXXXXXXXXXXX",
  "id_sesion_mesa": "01KAASS2HQGS37Q42YQ6XXJZWR",
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ", // ⬅️ MISMO TOKEN
  "message": "Login exitoso",
  "fecha_expiracion": "2025-11-18T03:00:00"
}
```

**IMPORTANTE**: Todos los usuarios de la mesa reciben el **mismo token de sesión**.

---

### FASE 3: Creación de Pedidos

#### Paso 3.1: Usuario selecciona productos en el frontend
El usuario elige:
- Productos del menú (solo necesita `id_producto`)
- Cantidad de cada producto
- Opciones adicionales (ej: tamaño, extras) - solo necesita `id_producto_opcion`
- Notas de personalización (opcional)

#### Paso 3.2: Frontend construye el request
```json
{
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
  "items": [
    {
      "id_producto": "01KA9V0NKXVRWJVE9RGYCTQX49",
      "cantidad": 2,
      "opciones": [
        {
          "id_producto_opcion": "01KA9V0NKXVRWJVE9RGYCTQX50"
        }
      ],
      "notas_personalizacion": "Sin cebolla, por favor"
    }
  ],
  "notas_cliente": "Alérgico a mariscos",
  "notas_cocina": "Urgente para mesa VIP"
}
```

**NOTA IMPORTANTE**: El frontend **NO envía precios**. El backend los obtiene desde la base de datos.

#### Paso 3.3: Backend recibe el request en `/pedidos/enviar`

#### Paso 3.4: Backend busca la sesión por token
```
Query:
  SELECT * FROM sesiones_mesas WHERE token_sesion = ?
```

**Caso A: Sesión NO existe**
- ERROR 404: "No se encontró la sesión de mesa con token 'XXX'"

**Caso B: Sesión existe**
- Continúa al Paso 3.5

#### Paso 3.5: Backend valida el estado de la sesión
```
Validación:
  sesion.estado == EstadoSesionMesa.ACTIVA
```

**Caso A: Sesión NO está activa (CERRADA, FINALIZADA, INACTIVA)**
- ERROR 400: "La sesión de mesa no está activa. No se pueden crear pedidos."

**Caso B: Sesión está ACTIVA**
- Continúa al Paso 3.6

#### Paso 3.6: Backend obtiene precios de productos desde la BD
Para cada item del pedido:

```
Query para producto:
  SELECT precio_base FROM productos WHERE id = ?

Query para cada opción:
  SELECT precio_adicional FROM productos_opciones WHERE id = ?
```

#### Paso 3.7: Backend calcula totales
```
Para cada item:
  precio_opciones = SUM(precio_adicional de cada opción)
  subtotal_item = cantidad * (precio_base + precio_opciones)

Totales del pedido:
  subtotal = SUM(subtotal_item de todos los items)
  impuestos = subtotal * 0.18 (18% IGV en Perú)
  descuentos = 0 (por defecto)
  total = subtotal + impuestos - descuentos
```

#### Paso 3.8: Backend genera número de pedido
```
Formato: YYYYMMDD-M{numero_mesa}-{secuencia}
Ejemplo: 20251118-M1-005

Cálculo de secuencia:
  - Contar pedidos de hoy para esta mesa
  - Incrementar contador
```

#### Paso 3.9: Backend crea registros en la BD

**3.9.1: Crea el pedido**
```sql
INSERT INTO pedidos (
  id, id_sesion_mesa, numero_pedido, estado,
  subtotal, impuestos, descuentos, total,
  notas_cliente, notas_cocina, fecha_creacion
) VALUES (...)
```

**3.9.2: Crea los productos del pedido**
```sql
Para cada item:
  INSERT INTO pedidos_productos (
    id, id_pedido, id_producto, cantidad,
    precio_unitario, precio_opciones, subtotal,
    notas_personalizacion
  ) VALUES (...)
```

**3.9.3: Crea las opciones de cada producto**
```sql
Para cada opción de cada item:
  INSERT INTO pedidos_opciones (
    id, id_pedido_producto, id_producto_opcion,
    precio_adicional
  ) VALUES (...)
```

#### Paso 3.10: Backend retorna respuesta
```json
{
  "status": 201,
  "message": "Pedido creado exitosamente",
  "pedido": {
    "id": "01KAASS2M4RD7XHBW2H22BR4Q0",
    "numero_pedido": "20251118-M1-006",
    "estado": "pendiente",
    "subtotal": 20.00,
    "impuestos": 0.00,
    "descuentos": 0.00,
    "total": 20.00,
    "notas_cliente": "Alérgico a mariscos",
    "notas_cocina": "Urgente para mesa VIP",
    "fecha_creacion": "2025-11-18T01:17:36",
    "productos": [...]
  }
}
```

---

### FASE 4: Consulta de Historial de Pedidos

#### Paso 4.1: Usuario solicita ver historial
El frontend llama a: `GET /pedidos/historial/{token_sesion}`

#### Paso 4.2: Backend busca la sesión por token
```
Query:
  SELECT * FROM sesiones_mesas WHERE token_sesion = ?
```

**Caso A: Sesión NO existe**
- ERROR 404: "No se encontró la sesión de mesa con token 'XXX'"

**Caso B: Sesión existe**
- Continúa al Paso 4.3

#### Paso 4.3: Backend verifica el estado de la sesión

**Caso A: Sesión está ACTIVA**
1. Backend busca todos los pedidos de la sesión:
   ```
   Query:
     SELECT * FROM pedidos
     WHERE id_sesion_mesa = ?
     ORDER BY fecha_creacion DESC
   ```
2. Backend retorna la lista completa de pedidos:
   ```json
   {
     "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
     "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
     "estado_sesion": "activa",
     "mensaje": null,
     "total_pedidos": 3,
     "pedidos": [...]
   }
   ```

**Caso B: Sesión está CERRADA o FINALIZADA**
1. Backend retorna lista vacía con mensaje:
   ```json
   {
     "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
     "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
     "estado_sesion": "cerrada",
     "mensaje": "Esta sesión ha sido cerrada o ha expirado. No hay pedidos disponibles.",
     "total_pedidos": 0,
     "pedidos": []
   }
   ```

**IMPORTANTE**:
- Los pedidos siguen existiendo en la BD (no se eliminan)
- Solo se ocultan del historial cuando la sesión está cerrada
- Esto es para proteger la privacidad después del cierre

---

### FASE 5: Cierre de Sesión

Existen dos formas de cerrar una sesión:

#### OPCIÓN A: Cierre Manual por Token

#### Paso 5A.1: Usuario solicita cerrar la sesión
El frontend llama a: `PATCH /sesiones-mesas/cerrar-por-token/{token_sesion}`

#### Paso 5A.2: Backend busca la sesión por token
```
Query:
  SELECT * FROM sesiones_mesas WHERE token_sesion = ?
```

**Caso A: Sesión NO existe**
- ERROR 404: "No se encontró la sesión de mesa con token 'XXX'"

**Caso B: Sesión existe**
- Continúa al Paso 5A.3

#### Paso 5A.3: Backend verifica si la sesión ya está cerrada
```
Validación:
  sesion.estado IN (EstadoSesionMesa.CERRADA, EstadoSesionMesa.FINALIZADA)
```

**Caso A: Sesión YA está cerrada**
- ERROR 400: "La sesión de mesa ya está cerrada"

**Caso B: Sesión NO está cerrada**
- Continúa al Paso 5A.4

#### Paso 5A.4: Backend actualiza la sesión
```sql
UPDATE sesiones_mesas
SET estado = 'CERRADA',
    fecha_fin = NOW()
WHERE id = ?
```

#### Paso 5A.5: Backend retorna respuesta
```json
{
  "id": "01KAASS2HQGS37Q42YQ6XXJZWR",
  "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
  "id_usuario_creador": "01KAANBJ4DG4A6H5TKBDEBKW72",
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
  "estado": "cerrada",
  "fecha_inicio": "2025-11-18T01:17:35",
  "fecha_fin": "2025-11-18T02:30:00",
  "fecha_creacion": "2025-11-18T01:17:35",
  "fecha_modificacion": "2025-11-18T02:30:00"
}
```

#### OPCIÓN B: Cierre Automático por Expiración

#### Paso 5B.1: Sistema verifica sesiones expiradas
El sistema tiene un endpoint administrativo: `POST /admin/sesiones/finalizar-expiradas`

Este endpoint se puede ejecutar mediante:
- Un cron job (tarea programada cada X minutos)
- Manualmente por un administrador

#### Paso 5B.2: Backend busca sesiones expiradas
```
Query:
  SELECT * FROM sesiones_mesas
  WHERE estado = 'ACTIVA'
    AND fecha_inicio + (duracion_minutos * INTERVAL '1 minute') < NOW()
```

#### Paso 5B.3: Para cada sesión expirada
```sql
UPDATE sesiones_mesas
SET estado = 'FINALIZADA',
    fecha_fin = NOW()
WHERE id = ?
```

#### Paso 5B.4: Backend retorna resumen
```json
{
  "total_finalizadas": 5,
  "sesiones_finalizadas": [
    {
      "id_sesion": "01KAASS2HQGS37Q42YQ6XXJZWR",
      "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
      "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
      "fecha_inicio": "2025-11-18T01:17:35",
      "fecha_expiracion": "2025-11-18T03:17:35",
      "minutos_expirada": 15
    }
  ],
  "message": "Sesiones expiradas finalizadas correctamente"
}
```

---

### FASE 6: Comportamiento Post-Cierre

#### Intento de crear pedido con sesión cerrada

**Request:**
```
POST /pedidos/enviar
{
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ", // Token de sesión cerrada
  "items": [...]
}
```

**Response:**
```
Status: 400 Bad Request
{
  "detail": "La sesión de mesa no está activa. No se pueden crear pedidos."
}
```

#### Consulta de historial con sesión cerrada

**Request:**
```
GET /pedidos/historial/01KAASS2HQWQXRH4D31F6Z8BZQ
```

**Response:**
```
Status: 200 OK
{
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
  "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
  "estado_sesion": "cerrada",
  "mensaje": "Esta sesión ha sido cerrada o ha expirado. No hay pedidos disponibles.",
  "total_pedidos": 0,
  "pedidos": []
}
```

---

## Escenarios Específicos

### Escenario 1: Cuatro Usuarios Llegan Juntos

**Contexto**: Mesa para 4 personas, todos llegan al mismo tiempo.

**Timeline:**
```
T+0s: Usuario 1 escanea QR → Crea sesión → Token: ABC123
T+5s: Usuario 2 escanea QR → Se une a sesión → Token: ABC123 (mismo)
T+8s: Usuario 3 escanea QR → Se une a sesión → Token: ABC123 (mismo)
T+12s: Usuario 4 escanea QR → Se une a sesión → Token: ABC123 (mismo)
```

**Resultado:**
- 1 sesión creada
- 4 usuarios asociados a la misma sesión
- 4 usuarios con el mismo token
- Todos pueden hacer pedidos
- El historial muestra los pedidos de todos

---

### Escenario 2: Usuario Sale y Regresa

**Contexto**: Usuario sale del restaurante y regresa después de 30 minutos.

**Timeline:**
```
T+0m: Usuario hace login → Obtiene token ABC123
T+15m: Usuario hace un pedido exitosamente
T+30m: Usuario sale (cierra app)
T+60m: Usuario regresa y vuelve a escanear el QR
```

**Comportamiento:**

**Si la sesión sigue activa (no expiró):**
1. Sistema encuentra la sesión existente
2. Verifica que el usuario ya está en la sesión
3. Retorna el mismo token ABC123
4. Usuario puede seguir haciendo pedidos
5. Ve el historial completo (incluyendo su pedido anterior)

**Si la sesión expiró:**
1. Sistema detecta sesión expirada
2. Finaliza la sesión antigua (estado → FINALIZADA)
3. Crea una NUEVA sesión con nuevo token XYZ789
4. Usuario recibe el nuevo token
5. Historial de la sesión anterior YA NO está visible

---

### Escenario 3: Dos Grupos en la Misma Mesa (Turnos)

**Contexto**:
- Primer grupo: 11:00 AM - 12:30 PM
- Segundo grupo: 2:00 PM - 3:30 PM

**Timeline Grupo 1:**
```
11:00 AM: Usuario 1A hace login → Crea sesión → Token: ABC123
11:05 AM: Usuarios 2A, 3A, 4A se unen → Token: ABC123
11:10 AM - 12:20 PM: Hacen varios pedidos
12:30 PM: Cierran la sesión manualmente → Estado: CERRADA
```

**Timeline Grupo 2:**
```
2:00 PM: Usuario 1B hace login
  - Sistema busca sesión activa para la mesa
  - Encuentra sesión ABC123 pero está CERRADA
  - Crea NUEVA sesión → Token: XYZ789
2:05 PM: Usuarios 2B, 3B se unen → Token: XYZ789
2:10 PM - 3:20 PM: Hacen pedidos (independientes del primer grupo)
3:30 PM: Sesión expira automáticamente → Estado: FINALIZADA
```

**Resultado:**
- 2 sesiones completamente independientes
- Cada grupo ve solo sus propios pedidos
- Los tokens son diferentes
- Los historiales están separados

---

### Escenario 4: Sesión Expira Durante el Uso

**Contexto**: Sesión con duración de 120 minutos, usuarios llegan tarde.

**Timeline:**
```
1:00 PM: Usuario 1 crea sesión → Token: ABC123 (expira a las 3:00 PM)
1:30 PM: Usuarios 2, 3, 4 se unen
1:35 PM - 2:50 PM: Hacen varios pedidos
2:58 PM: Usuario intenta hacer otro pedido → ✅ ÉXITO (sesión aún activa)
3:02 PM: Usuario intenta hacer otro pedido → ❌ ERROR
```

**Comportamiento a las 3:02 PM:**

**Intento de crear pedido:**
```
Request: POST /pedidos/enviar con token ABC123
Response: ERROR 400 "La sesión de mesa no está activa"
```

**Usuario vuelve a escanear QR:**
1. Sistema detecta sesión expirada
2. Finaliza sesión ABC123 (estado → FINALIZADA)
3. Crea NUEVA sesión XYZ789
4. Usuario recibe nuevo token
5. Puede seguir haciendo pedidos con el nuevo token

**IMPORTANTE**: Los pedidos anteriores (hechos antes de las 3:00 PM) se CONSERVAN en la BD pero ya NO son visibles en el historial con el nuevo token.

---

### Escenario 5: Múltiples Intentos de Login del Mismo Usuario

**Contexto**: Usuario escanea el QR múltiples veces por error.

**Timeline:**
```
T+0s: Usuario 1 escanea QR → Crea sesión → Token: ABC123
T+5s: Usuario 1 escanea QR de nuevo (app cerró por accidente)
T+10s: Usuario 1 escanea QR de nuevo (no confía del primero)
```

**Comportamiento:**

**Primer escaneo (T+0s):**
1. Crea usuario (si no existe)
2. Crea sesión
3. Crea asociación usuario-sesión
4. Retorna token ABC123

**Segundo escaneo (T+5s):**
1. Encuentra usuario existente (por email)
2. Actualiza ultimo_acceso
3. Encuentra sesión activa para la mesa
4. Verifica que el usuario YA está en la sesión
5. NO crea nueva asociación (reutiliza la existente)
6. Retorna el MISMO token ABC123

**Tercer escaneo (T+10s):**
1. Mismo comportamiento que el segundo escaneo
2. Retorna el MISMO token ABC123

**Resultado:**
- 1 sesión creada
- 1 asociación usuario-sesión creada
- Usuario recibe el mismo token en todas las ocasiones
- NO se crean registros duplicados

---

## Validaciones y Reglas de Negocio

### Validaciones en Login

#### 1. Validación de Email
```
Regla: Debe contener "correo", "mail" o "@"
Ejemplos válidos:
  - usuario@example.com
  - usuario.correo.com
  - usuario_mail
Ejemplos inválidos:
  - usuario123
  - nombreusuario
```

#### 2. Validación de Mesa
```
Regla: La mesa debe existir en la BD
Query: SELECT * FROM mesas WHERE id = ?
Si no existe: ERROR "No se encontró la mesa con ID 'XXX'"
```

#### 3. Unicidad de Sesión Activa por Mesa
```
Regla: Solo puede existir UNA sesión ACTIVA por mesa
Query:
  SELECT COUNT(*) FROM sesiones_mesas
  WHERE id_mesa = ? AND estado = 'ACTIVA'
Si COUNT > 1: Situación anómala (se debe corregir con endpoint de admin)
```

---

### Validaciones en Creación de Pedidos

#### 1. Validación de Token
```
Regla: El token debe tener exactamente 26 caracteres (ULID)
Regla: El token debe ser alfanumérico
Validación: Se normaliza a UPPERCASE
```

#### 2. Validación de Sesión Activa
```
Regla: La sesión debe existir
Regla: La sesión debe estar en estado ACTIVA
Si no cumple: ERROR 400 "La sesión de mesa no está activa. No se pueden crear pedidos."
```

#### 3. Validación de Productos
```
Regla: Todos los id_producto deben existir en la BD
Regla: Los productos deben estar disponibles (disponible = true)
Query: SELECT * FROM productos WHERE id = ? AND disponible = true
Si no existe: ERROR 404 "Producto no encontrado"
```

#### 4. Validación de Opciones
```
Regla: Todos los id_producto_opcion deben existir en la BD
Regla: Las opciones deben estar activas (activo = true)
Regla: Las opciones deben pertenecer al producto seleccionado
Query:
  SELECT * FROM productos_opciones
  WHERE id = ?
    AND id_producto = ?
    AND activo = true
Si no cumple: ERROR 400 "Opción no válida para este producto"
```

#### 5. Validación de Cantidades
```
Regla: Cantidad mínima: 1
Regla: Cantidad máxima: 99
Si no cumple: ERROR 400 "Cantidad debe estar entre 1 y 99"
```

#### 6. Validación de Notas
```
Regla: notas_cliente máximo 1000 caracteres
Regla: notas_cocina máximo 1000 caracteres
Regla: notas_personalizacion (por producto) máximo 500 caracteres
Si excede: ERROR 400 "Notas exceden el límite de caracteres"
```

---

### Validaciones en Cierre de Sesión

#### 1. Validación de Existencia
```
Regla: La sesión debe existir
Query: SELECT * FROM sesiones_mesas WHERE token_sesion = ?
Si no existe: ERROR 404 "No se encontró la sesión de mesa con token 'XXX'"
```

#### 2. Validación de Estado
```
Regla: La sesión NO debe estar ya cerrada o finalizada
Validación: estado NOT IN ('CERRADA', 'FINALIZADA')
Si ya está cerrada: ERROR 400 "La sesión de mesa ya está cerrada"
```

---

## Modelos de Datos

### Tabla: `sesiones_mesas`

```sql
CREATE TABLE sesiones_mesas (
    id VARCHAR(36) PRIMARY KEY,              -- ULID
    id_mesa VARCHAR(36) NOT NULL,            -- FK a mesas
    id_usuario_creador VARCHAR(36) NOT NULL, -- FK a usuarios
    token_sesion VARCHAR(100) NOT NULL UNIQUE,
    estado VARCHAR(20) NOT NULL,             -- ENUM: activa, inactiva, cerrada, finalizada
    fecha_inicio TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_fin TIMESTAMP NULL,
    duracion_minutos INTEGER NOT NULL DEFAULT 120,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT NOW(),

    FOREIGN KEY (id_mesa) REFERENCES mesas(id) ON DELETE RESTRICT,
    FOREIGN KEY (id_usuario_creador) REFERENCES usuarios(id) ON DELETE RESTRICT,

    CONSTRAINT chk_sesion_mesa_fecha_fin_valida
        CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio),

    INDEX idx_sesion_mesa_mesa (id_mesa),
    INDEX idx_sesion_mesa_token (token_sesion),
    INDEX idx_sesion_mesa_estado (estado)
);
```

### Tabla: `usuarios_sesiones_mesas`

```sql
CREATE TABLE usuarios_sesiones_mesas (
    id VARCHAR(36) PRIMARY KEY,              -- ULID
    id_usuario VARCHAR(36) NOT NULL,         -- FK a usuarios
    id_sesion_mesa VARCHAR(36) NOT NULL,     -- FK a sesiones_mesas
    fecha_ingreso TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT NOW(),

    FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (id_sesion_mesa) REFERENCES sesiones_mesas(id) ON DELETE CASCADE,

    UNIQUE CONSTRAINT uq_usuario_sesion_mesa (id_usuario, id_sesion_mesa),

    INDEX idx_usuario_sesion_mesa_usuario (id_usuario),
    INDEX idx_usuario_sesion_mesa_sesion (id_sesion_mesa)
);
```

### Tabla: `pedidos` (simplificada)

```sql
CREATE TABLE pedidos (
    id VARCHAR(36) PRIMARY KEY,              -- ULID
    id_sesion_mesa VARCHAR(36) NOT NULL,     -- FK a sesiones_mesas
    numero_pedido VARCHAR(50) NOT NULL,      -- YYYYMMDD-M#-SEQ
    estado VARCHAR(20) NOT NULL,             -- ENUM: pendiente, confirmado, en_preparacion, listo, entregado, cancelado
    subtotal DECIMAL(10,2) NOT NULL,
    impuestos DECIMAL(10,2) NOT NULL DEFAULT 0,
    descuentos DECIMAL(10,2) NOT NULL DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    notas_cliente TEXT NULL,
    notas_cocina TEXT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_confirmado TIMESTAMP NULL,
    fecha_en_preparacion TIMESTAMP NULL,
    fecha_listo TIMESTAMP NULL,
    fecha_entregado TIMESTAMP NULL,

    FOREIGN KEY (id_sesion_mesa) REFERENCES sesiones_mesas(id),

    UNIQUE CONSTRAINT uq_numero_pedido (numero_pedido),

    INDEX idx_pedido_sesion (id_sesion_mesa),
    INDEX idx_pedido_numero (numero_pedido),
    INDEX idx_pedido_estado (estado)
);
```

---

## Endpoints API

### Autenticación y Sesiones

#### 1. Login (Crear o Unirse a Sesión)

```http
POST /mesas/{id_mesa}/login
Content-Type: application/json

{
  "email": "usuario@example.com",
  "nombre": "Juan Pérez"
}
```

**Response 200 OK:**
```json
{
  "status": 200,
  "code": "SUCCESS",
  "id_usuario": "01KAANBJ4DG4A6H5TKBDEBKW72",
  "id_sesion_mesa": "01KAASS2HQGS37Q42YQ6XXJZWR",
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
  "message": "Login exitoso",
  "fecha_expiracion": "2025-11-18T03:17:35"
}
```

---

### Pedidos

#### 2. Crear Pedido con Token de Sesión

```http
POST /pedidos/enviar
Content-Type: application/json

{
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
  "items": [
    {
      "id_producto": "01KA9V0NKXVRWJVE9RGYCTQX49",
      "cantidad": 2,
      "opciones": [
        {
          "id_producto_opcion": "01KA9V0NKXVRWJVE9RGYCTQX50"
        }
      ],
      "notas_personalizacion": "Sin cebolla"
    }
  ],
  "notas_cliente": "Alérgico a mariscos",
  "notas_cocina": "Urgente"
}
```

**Response 201 Created:**
```json
{
  "status": 201,
  "message": "Pedido creado exitosamente",
  "pedido": {
    "id": "01KAASS2M4RD7XHBW2H22BR4Q0",
    "numero_pedido": "20251118-M1-006",
    "estado": "pendiente",
    "subtotal": 20.00,
    "impuestos": 3.60,
    "descuentos": 0.00,
    "total": 23.60,
    "notas_cliente": "Alérgico a mariscos",
    "notas_cocina": "Urgente",
    "fecha_creacion": "2025-11-18T01:17:36",
    "productos": [...]
  }
}
```

#### 3. Obtener Historial de Pedidos por Token

```http
GET /pedidos/historial/{token_sesion}
```

**Response 200 OK (sesión activa):**
```json
{
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
  "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
  "estado_sesion": "activa",
  "mensaje": null,
  "total_pedidos": 3,
  "pedidos": [
    {
      "id": "01KAASS2M4RD7XHBW2H22BR4Q0",
      "numero_pedido": "20251118-M1-006",
      "estado": "pendiente",
      "subtotal": 20.00,
      "total": 23.60,
      "productos": [...]
    }
  ]
}
```

**Response 200 OK (sesión cerrada):**
```json
{
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
  "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
  "estado_sesion": "cerrada",
  "mensaje": "Esta sesión ha sido cerrada o ha expirado. No hay pedidos disponibles.",
  "total_pedidos": 0,
  "pedidos": []
}
```

---

### Gestión de Sesiones

#### 4. Cerrar Sesión por Token

```http
PATCH /sesiones-mesas/cerrar-por-token/{token_sesion}
```

**Response 200 OK:**
```json
{
  "id": "01KAASS2HQGS37Q42YQ6XXJZWR",
  "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
  "id_usuario_creador": "01KAANBJ4DG4A6H5TKBDEBKW72",
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
  "estado": "cerrada",
  "fecha_inicio": "2025-11-18T01:17:35",
  "fecha_fin": "2025-11-18T02:30:00",
  "fecha_creacion": "2025-11-18T01:17:35",
  "fecha_modificacion": "2025-11-18T02:30:00"
}
```

#### 5. Obtener Sesión por ID

```http
GET /sesiones-mesas/{sesion_id}
```

**Response 200 OK:**
```json
{
  "id": "01KAASS2HQGS37Q42YQ6XXJZWR",
  "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
  "id_usuario_creador": "01KAANBJ4DG4A6H5TKBDEBKW72",
  "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
  "estado": "activa",
  "fecha_inicio": "2025-11-18T01:17:35",
  "fecha_fin": null,
  "fecha_creacion": "2025-11-18T01:17:35",
  "fecha_modificacion": "2025-11-18T01:17:35"
}
```

#### 6. Listar Sesiones de Mesa (con filtros)

```http
GET /sesiones-mesas/?skip=0&limit=10&id_mesa={id_mesa}&estado=activa
```

**Response 200 OK:**
```json
{
  "total": 25,
  "page": 1,
  "limit": 10,
  "sesiones": [
    {
      "id": "01KAASS2HQGS37Q42YQ6XXJZWR",
      "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
      "id_usuario_creador": "01KAANBJ4DG4A6H5TKBDEBKW72",
      "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
      "estado": "activa",
      "fecha_inicio": "2025-11-18T01:17:35",
      "fecha_fin": null,
      "fecha_creacion": "2025-11-18T01:17:35",
      "fecha_modificacion": "2025-11-18T01:17:35"
    }
  ]
}
```

---

### Endpoints de Administración

#### 7. Finalizar Sesiones Expiradas (Admin)

```http
POST /admin/sesiones/finalizar-expiradas
```

**Response 200 OK:**
```json
{
  "total_finalizadas": 5,
  "sesiones_finalizadas": [
    {
      "id_sesion": "01KAASS2HQGS37Q42YQ6XXJZWR",
      "token_sesion": "01KAASS2HQWQXRH4D31F6Z8BZQ",
      "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
      "fecha_inicio": "2025-11-18T01:17:35",
      "fecha_expiracion": "2025-11-18T03:17:35",
      "minutos_expirada": 15
    }
  ],
  "message": "Sesiones expiradas finalizadas correctamente"
}
```

#### 8. Obtener Estado de Sesiones (Admin)

```http
GET /admin/sesiones/estado
```

**Response 200 OK:**
```json
{
  "total_sesiones": 150,
  "activas": 12,
  "inactivas": 3,
  "cerradas": 85,
  "finalizadas": 50,
  "sesiones_duplicadas": []
}
```

#### 9. Corregir Sesiones Duplicadas (Admin)

```http
POST /admin/sesiones/fix-duplicadas
```

**Response 200 OK:**
```json
{
  "total_corregidas": 2,
  "sesiones_finalizadas": [
    {
      "id_sesion": "01KAASS2HQGS37Q42YQ6XXJZWR",
      "id_mesa": "01KA9V0NKXVRWJVE9RGYCTQX49",
      "razon": "Sesión duplicada (más antigua)"
    }
  ],
  "message": "Sesiones duplicadas corregidas"
}
```

---

## Resumen de Restricciones y Límites

### Límites del Sistema

| Concepto | Límite | Descripción |
|----------|--------|-------------|
| Usuarios por sesión | Sin límite técnico | Todos pueden unirse con el mismo token |
| Sesiones activas por mesa | 1 | Solo una sesión ACTIVA por mesa |
| Duración por defecto | 120 minutos | Configurable en `duracion_minutos` |
| Cantidad por producto | 1 - 99 | Rango permitido en cada item |
| Longitud de token | 26 caracteres | ULID estándar |
| Notas de cliente | 1000 caracteres | Máximo permitido |
| Notas de cocina | 1000 caracteres | Máximo permitido |
| Notas por producto | 500 caracteres | Máximo permitido |
| Pedidos por sesión | Sin límite | Se pueden crear múltiples pedidos |

### Restricciones de Estado

| Estado Actual | Puede crear pedidos | Puede verse historial | Puede cerrarse |
|---------------|--------------------|-----------------------|----------------|
| ACTIVA | ✅ Sí | ✅ Sí | ✅ Sí |
| INACTIVA | ❌ No | ✅ Sí | ✅ Sí |
| CERRADA | ❌ No | ❌ No (lista vacía) | ❌ No (ya cerrada) |
| FINALIZADA | ❌ No | ❌ No (lista vacía) | ❌ No (ya cerrada) |

---

## Diagrama de Estados

```
                          ┌─────────┐
                          │ ACTIVA  │ ◄─── Estado inicial (al crear)
                          └────┬────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                │              │              │
                ▼              ▼              ▼
         ┌──────────┐   ┌──────────┐   ┌──────────┐
         │ INACTIVA │   │ CERRADA  │   │FINALIZADA│
         └────┬─────┘   └──────────┘   └──────────┘
              │              ▲              ▲
              │              │              │
              └──────────────┴──────────────┘
                  (Estados finales)
```

**Transiciones:**
- `ACTIVA` → `CERRADA`: Cierre manual por token
- `ACTIVA` → `FINALIZADA`: Expiración automática
- `ACTIVA` → `INACTIVA`: Actualización manual (admin)
- `INACTIVA` → `CERRADA`: Cierre manual
- `INACTIVA` → `FINALIZADA`: Expiración automática

---

## Consideraciones de Seguridad y Privacidad

### 1. Protección del Token
- El token de sesión NO debe compartirse fuera del grupo de la mesa
- El token permite crear pedidos sin autenticación adicional
- El token tiene una duración limitada (120 minutos por defecto)

### 2. Privacidad Post-Cierre
- Una vez cerrada la sesión, el historial retorna vacío
- Los pedidos siguen existiendo en la BD (para reportes y contabilidad)
- Nuevos usuarios NO pueden ver pedidos de sesiones anteriores

### 3. Prevención de Duplicados
- El sistema previene crear múltiples sesiones activas para la misma mesa
- El endpoint de admin puede corregir sesiones duplicadas (casos excepcionales)

### 4. Trazabilidad
- Cada pedido está vinculado a una sesión específica
- Cada sesión tiene un usuario creador registrado
- Todos los cambios de estado tienen timestamps

---

## Notas de Implementación

### Backend
- **Framework**: FastAPI con Python
- **ORM**: SQLAlchemy con AsyncIO
- **Validación**: Pydantic schemas
- **IDs**: ULID (26 caracteres alfanuméricos)
- **Base de datos**: PostgreSQL o SQLite

### Cron Job Recomendado
```bash
# Ejecutar cada 15 minutos para finalizar sesiones expiradas
*/15 * * * * curl -X POST http://localhost:8000/admin/sesiones/finalizar-expiradas
```

### Logs Recomendados
- Creación de sesión (con id_mesa, id_usuario_creador, token)
- Unión de usuario a sesión (con id_usuario, id_sesion_mesa)
- Creación de pedido (con id_pedido, token_sesion, total)
- Cierre de sesión (con id_sesion, tipo_cierre: manual/auto)

---

## Conclusión

Este documento describe el flujo completo de sesiones de mesa en el sistema del restaurante. El diseño permite:

✅ **Colaboración**: Múltiples usuarios comparten la misma sesión y token
✅ **Simplicidad**: Login con solo email y nombre (no requiere contraseña)
✅ **Seguridad**: Tokens únicos con expiración automática
✅ **Privacidad**: Historial vacío después del cierre
✅ **Escalabilidad**: Sin límite de usuarios por sesión
✅ **Trazabilidad**: Registro completo de todos los eventos

Este flujo está diseñado para maximizar la experiencia del usuario en un restaurante, permitiendo que grupos de personas puedan hacer pedidos de forma colaborativa sin fricciones técnicas.
