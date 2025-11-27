# 📊 Guía Completa de Diagramas - Sistema de Sesiones de Mesa

## 📁 Contenido Generado

Se han creado **10 diagramas PNG** en alta resolución (300 DPI) con orientación horizontal, ideales para presentaciones y documentación técnica.

---

## 📋 Índice de Diagramas

### 1️⃣ **01_MACRO_Sistema_Completo.png**
**Propósito**: Visión general del sistema completo  
**Audiencia**: Stakeholders, gerencia, overview técnico  
**Contenido**:
- Flujo desde que el usuario escanea el QR hasta que finaliza la sesión
- Muestra las 5 fases principales del sistema
- Indica los loops de operaciones (crear pedidos, ver historial)
- Incluye tanto cierre manual como automático por expiración
- **Uso recomendado**: Primera slide de presentaciones, documentación de alto nivel

### 2️⃣ **02_FASE1_Primer_Usuario.png**
**Propósito**: Detalle completo del proceso de login del primer usuario  
**Audiencia**: Desarrolladores, testers, analistas de negocio  
**Contenido**:
- Escaneo de QR y captura de datos (email + nombre)
- Validación de formato de email (debe contener "correo", "mail" o "@")
- Lógica de creación/búsqueda de usuario
- Actualización de campos si el usuario ya existe
- Creación de la nueva sesión (token único, estado ACTIVA)
- Asociación del usuario con la sesión
- Cálculo de fecha de expiración (fecha_inicio + 120 minutos)
- Response JSON con token_sesion
- **Casos especiales**: Manejo de usuario nuevo vs existente, actualización de nombre

### 3️⃣ **03_FASE2_Usuarios_Adicionales.png**
**Propósito**: Detalle del proceso cuando usuarios adicionales se unen a la mesa  
**Audiencia**: Desarrolladores, testers  
**Contenido**:
- Proceso de login (similar a Fase 1)
- Búsqueda de sesión ACTIVA existente
- Validación de expiración de sesión
- **Caso A**: Sesión válida → Asociar usuario
- **Caso B**: Sesión expirada → Finalizar vieja y crear nueva
- Verificación si el usuario ya está en la sesión (evitar duplicados)
- Retorno del **MISMO token_sesion** que otros usuarios
- **Concepto clave**: Token compartido entre todos los usuarios de la mesa

### 4️⃣ **04_FASE3_Crear_Pedidos.png**
**Propósito**: Flujo completo de creación de pedidos con todas las validaciones  
**Audiencia**: Desarrolladores backend, testers de QA  
**Contenido**:
- **Validaciones en cascada**:
  - Token_sesion existe
  - Sesión está en estado ACTIVA
  - Items no está vacío
  - Para cada producto: existe, está disponible, cantidad 1-99, stock suficiente
- Cálculo de totales (subtotal + IGV 18%)
- Generación de número de pedido (formato: YYYYMMDD-MX-NNN)
- Creación de registro PedidoMesaModel
- Creación de ItemPedidoMesaModel para cada producto
- Actualización de stock (stock_actual -= cantidad)
- Commit de transacción
- **Manejo de errores**: Muestra todos los errores 400/404 posibles

### 5️⃣ **05_FASE4_Consultar_Historial.png**
**Propósito**: Flujo de consulta de historial de pedidos  
**Audiencia**: Desarrolladores, diseñadores UX  
**Contenido**:
- Validación de token_sesion
- Verificación de estado de sesión
- **Caso 1**: Sesión CERRADA/FINALIZADA → Retorna lista vacía (privacidad)
- **Caso 2**: Sesión ACTIVA/INACTIVA → Retorna todos los pedidos
- Carga de items con productos (JOINs)
- Estructura de response con array de pedidos
- **Concepto de privacidad**: Historial vacío post-cierre

### 6️⃣ **06_FASE5_Cerrar_Sesion.png**
**Propósito**: Proceso de cierre de sesión (manual y automático)  
**Audiencia**: Desarrolladores, administradores de sistema  
**Contenido**:
- **Dos tipos de inicio**:
  - Manual: Usuario solicita cierre vía endpoint
  - Automático: Sistema detecta sesión expirada (>120 min)
- Validación de token y estado
- Actualización de estado:
  - CERRADA (cierre manual)
  - FINALIZADA (cierre automático)
- Campo fecha_fin = NOW()
- **Cron Job**: Referencia al endpoint de admin para finalizar sesiones expiradas cada 15 min

### 7️⃣ **07_Estados_Sesion.png**
**Propósito**: Máquina de estados de una sesión  
**Audiencia**: Arquitectos, desarrolladores, documentación técnica  
**Contenido**:
- **4 estados posibles**:
  - ACTIVA (inicial, operativa)
  - INACTIVA (temporal, deshabilitada)
  - CERRADA (final, cierre manual)
  - FINALIZADA (final, expiración automática)
- **Transiciones permitidas**:
  - ACTIVA → INACTIVA (manual admin)
  - ACTIVA → CERRADA (cierre manual)
  - ACTIVA → FINALIZADA (expiración)
  - INACTIVA → CERRADA (cierre manual)
  - INACTIVA → FINALIZADA (expiración)
- **Permisos por estado**: Qué operaciones se pueden realizar en cada estado
- **Estados finales**: CERRADA y FINALIZADA no tienen vuelta atrás

### 8️⃣ **08_Modelo_Datos_ER.png**
**Propósito**: Diagrama Entidad-Relación del modelo de datos  
**Audiencia**: Arquitectos de datos, DBAs, desarrolladores backend  
**Contenido**:
- **7 entidades principales**:
  - UsuarioModel
  - MesaModel
  - SesionMesaModel (entidad central)
  - UsuarioSesionMesaModel (tabla Many-to-Many)
  - PedidoMesaModel
  - ItemPedidoMesaModel
  - ProductoModel
- **Relaciones con cardinalidades**:
  - Mesa 1:N Sesiones
  - Usuario 1:N Sesiones (creador)
  - Usuario M:N Sesiones (vía UsuarioSesionMesaModel)
  - Sesión 1:N Pedidos
  - Pedido 1:N Items
  - Producto 1:N Items
- **Atributos clave**: IDs (ULID), campos de fecha, estados (Enum), constraints

### 9️⃣ **09_Arquitectura_Endpoints.png**
**Propósito**: Arquitectura de API y organización de endpoints  
**Audiencia**: Desarrolladores frontend/backend, arquitectos  
**Contenido**:
- **4 grupos de endpoints**:
  1. **LOGIN/AUTH**: POST /login-mesa
  2. **PEDIDOS**: POST /pedidos-mesa, GET /pedidos-mesa/historial/{token}
  3. **GESTIÓN SESIONES**: GET /sesiones-mesas/{id}, GET /sesiones-mesas/, PATCH /sesiones-mesas/cerrar-por-token/{token}
  4. **ADMIN**: POST /admin/sesiones/finalizar-expiradas, GET /admin/sesiones/estado, POST /admin/sesiones/fix-duplicadas
- Flujo de datos entre cliente → endpoints → base de datos
- **Cron Job**: Ejecución cada 15 min para finalizar sesiones expiradas
- **Nota de autenticación**: Sin JWT tradicional, usa token_sesion compartido

### 🔟 **10_Validaciones_Errores.png**
**Propósito**: Mapa completo de validaciones y manejo de errores  
**Audiencia**: Testers QA, desarrolladores, analistas de negocio  
**Contenido**:
- **7 tipos de validación**:
  1. **Email**: Debe contener "correo", "mail" o "@"
  2. **Token**: Debe existir en BD (26 caracteres)
  3. **Estado sesión**: ACTIVA para crear pedidos, ACTIVA/INACTIVA para ver historial
  4. **Productos**: Existe, disponible, cantidad 1-99, stock suficiente
  5. **Sesión única**: Solo 1 ACTIVA por mesa
  6. **Expiración**: NOW() vs fecha_inicio + duracion_minutos
  7. **Notas**: Límites de caracteres (500-1000)
- **Códigos de error HTTP**:
  - 400: Bad Request (validaciones de negocio)
  - 404: Not Found (token no existe)
- **Casos especiales**: Sesión expirada se finaliza y se crea nueva automáticamente

---

## 🎨 Características de los Diagramas

### Colores y Significado
- 🟢 **Verde claro**: Estados exitosos, inicio/fin
- 🔵 **Azul claro**: Procesos normales
- 🟡 **Amarillo**: Decisiones, validaciones, notas importantes
- 🔴 **Rojo claro**: Errores, estados finales negativos
- 🟠 **Naranja**: Advertencias, procesos automáticos

### Formas y Símbolos
- **Elipse**: Inicio/Fin de procesos
- **Rectángulo redondeado**: Procesos y acciones
- **Rombo**: Decisiones (sí/no)
- **Nota**: Información adicional importante
- **Cilindro**: Base de datos

### Orientación
- **Todos los diagramas**: Flujo horizontal de izquierda a derecha
- **Ideal para**: Presentaciones en pantallas wide, proyectores, impresión horizontal

---

## 📖 Cómo Usar Estos Diagramas

### Para Presentaciones Ejecutivas
1. Usar **01_MACRO** como introducción general
2. Mostrar **07_Estados** para explicar el ciclo de vida
3. Usar **08_Modelo_Datos** si hay interés técnico
4. Concluir con **09_Arquitectura_Endpoints**

### Para Documentación Técnica
1. Incluir **todos los diagramas** en orden
2. Comenzar con MACRO, luego FASES 1-5 en secuencia
3. Agregar Estados y Modelo de Datos
4. Finalizar con Endpoints y Validaciones

### Para Desarrollo y Testing
- **Desarrolladores Frontend**: FASE 1, 2, 3, 4, 5 + Endpoints
- **Desarrolladores Backend**: Todos, especialmente Modelo de Datos + Validaciones
- **QA/Testers**: FASE 3, 4, 5 + Validaciones (todos los casos de error)
- **DevOps**: FASE 5, Estados, Arquitectura (para cron jobs)

### Para Capacitación
1. Día 1: MACRO + FASE 1 + FASE 2 (flujo de usuarios)
2. Día 2: FASE 3 + FASE 4 (pedidos e historial)
3. Día 3: FASE 5 + Estados + Validaciones (cierre y seguridad)
4. Día 4: Modelo de Datos + Arquitectura (diseño técnico)

---

## 🔑 Conceptos Clave Ilustrados

### 1. Token Compartido
- **Diagramas**: 01, 02, 03
- Todos los usuarios de una mesa comparten el **mismo token_sesion**
- No hay autenticación por usuario, sino por mesa/sesión

### 2. Sesión Única por Mesa
- **Diagramas**: 02, 03, 10
- Solo puede haber 1 sesión ACTIVA por mesa simultáneamente
- Si existe sesión expirada, se finaliza y se crea nueva

### 3. Expiración Automática
- **Diagramas**: 03, 06, 07
- Duración por defecto: 120 minutos
- Sistema finaliza automáticamente vía cron job
- Estado final: FINALIZADA (vs CERRADA manual)

### 4. Privacidad Post-Cierre
- **Diagramas**: 05, 07
- Sesiones CERRADAS/FINALIZADAS retornan historial vacío
- Datos existen en BD pero no son accesibles vía API
- Protección de privacidad entre grupos

### 5. Validaciones en Cascada
- **Diagramas**: 04, 10
- Múltiples niveles de validación antes de crear pedido
- Fallo en cualquier validación = Error 400/404
- Transacción atómica: todo o nada

---

## 📊 Métricas de los Diagramas

| Diagrama | Tamaño | Nodos | Complejidad | Tiempo de Lectura |
|----------|--------|-------|-------------|-------------------|
| 01_MACRO | 492 KB | 15 | Media | 3-5 min |
| 02_FASE1 | 468 KB | 25+ | Alta | 8-10 min |
| 03_FASE2 | 497 KB | 25+ | Alta | 8-10 min |
| 04_FASE3 | 462 KB | 30+ | Muy Alta | 10-15 min |
| 05_FASE4 | 522 KB | 15 | Media | 5-7 min |
| 06_FASE5 | 432 KB | 20 | Media | 6-8 min |
| 07_Estados | 387 KB | 5 | Baja | 2-3 min |
| 08_Modelo_Datos | 697 KB | 7 entidades | Alta | 8-10 min |
| 09_Arquitectura | 588 KB | 10+ | Media | 5-7 min |
| 10_Validaciones | 1.2 MB | 35+ | Muy Alta | 12-15 min |

**Tiempo total de estudio completo**: ~70-90 minutos

---

## ✅ Verificación de Completitud

Todos los elementos del documento original están cubiertos:

- ✅ Visión General → Diagrama 01
- ✅ Conceptos Clave → Todos los diagramas
- ✅ Estados de la Sesión → Diagrama 07
- ✅ Flujo Completo Paso a Paso:
  - ✅ FASE 1 → Diagrama 02
  - ✅ FASE 2 → Diagrama 03
  - ✅ FASE 3 → Diagrama 04
  - ✅ FASE 4 → Diagrama 05
  - ✅ FASE 5 → Diagrama 06
- ✅ Escenarios Específicos → Cubiertos en Fases 2 y 3
- ✅ Validaciones y Reglas → Diagrama 10
- ✅ Modelos de Datos → Diagrama 08
- ✅ Endpoints API → Diagrama 09

---

## 🚀 Próximos Pasos Sugeridos

1. **Revisar cada diagrama** en orden secuencial (01 → 10)
2. **Imprimir los diagramas clave** para reuniones (01, 07, 08, 09)
3. **Compartir con el equipo** según roles (ver sección "Cómo Usar")
4. **Usar en documentación** técnica y presentaciones
5. **Actualizar según cambios** en el sistema

---

## 📝 Notas Importantes

- **Resolución**: 300 DPI (alta calidad para impresión)
- **Formato**: PNG (compatible con todos los sistemas)
- **Orientación**: Horizontal (ideal para pantallas wide)
- **Licencia**: Uso interno del proyecto
- **Versión**: Basado en documento FLUJO_SESIONES_MESA.md
- **Fecha**: 18 de Noviembre 2025

---

## 🆘 Soporte

Si necesitas modificaciones o diagramas adicionales:
- Modificar el script `/home/claude/generar_diagramas.py`
- Ejecutar: `python generar_diagramas.py`
- Los PNGs se regeneran en: `/mnt/user-data/outputs/diagramas/`

---

**¡Estos diagramas están listos para usar en presentaciones, documentación y capacitación!** 🎉
