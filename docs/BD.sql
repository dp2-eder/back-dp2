-- ============================================================================
--  ESQUEMA COMPLETO - Sistema de Gestión de Restaurante
--  IDs: ULID (26 chars, timestamp-ordered) con compatibilidad UUID v4 (36 chars)
--  Requiere MySQL 8.0+ (para CHECKs funcionales)
--
--  HISTORIAL DE VERSIONES:
--  -------------------------------------------------------------------------
--  v1.1.0 - 2025-10-29 - Actualización con nuevas tablas del backend
--    - NUEVAS TABLAS: local, zona, sesion (implementadas en backend)
--    - TABLAS ACTUALIZADAS: pedido, division_cuenta, division_cuenta_detalle,
--      pedido_producto (implementadas en backend)
--    - Campos de auditoría ajustados según implementación actual
--  v1.0.0 - 2025-10-23 - Versión inicial sincronizada con backend
--    - Tablas implementadas en backend: rol, categoria, alergeno, mesas,
--      producto, tipo_opcion, producto_opcion, producto_alergeno
--    - Tablas pendientes de implementación en backend: usuario, pedido,
--      pedido_producto, division_cuenta, division_cuenta_detalle,
--      pedido_opcion, pago
--    - CAMBIO en mesas: agregado campo 'nota' según modelo del backend
-- ============================================================================

-- Asegura un charset/collation consistente si hace falta:
-- SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- --------------------------------------------------------------------------
-- ROL
-- v1.0.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE rol (
    id                 CHAR(36) NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    nombre             VARCHAR(50)  NOT NULL,
    descripcion        VARCHAR(255) NULL,
    fecha_creacion     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP    DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)     NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)     NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT uq_rol_nombre UNIQUE (nombre)
) COMMENT='Roles del sistema (cliente, mesero, cocina, admin)';

CREATE INDEX idx_rol_creado_por     ON rol (creado_por);
CREATE INDEX idx_rol_modificado_por ON rol (modificado_por);


-- --------------------------------------------------------------------------
-- LOCAL
-- v1.1.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE local (
    id                 CHAR(36)     NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    codigo             VARCHAR(20)  NOT NULL COMMENT 'Código único del local (ej: CEV-001)',
    nombre             VARCHAR(100) NOT NULL COMMENT 'Nombre del local (ej: La Cevichería del Centro)',
    direccion          VARCHAR(255) NOT NULL COMMENT 'Dirección física del local',
    distrito           VARCHAR(100) NULL COMMENT 'Distrito donde se ubica el local',
    ciudad             VARCHAR(100) NULL COMMENT 'Ciudad donde se ubica el local',
    telefono           VARCHAR(20)  NULL COMMENT 'Número de teléfono del local',
    email              VARCHAR(100) NULL COMMENT 'Correo electrónico del local',
    tipo_local         ENUM('central', 'sucursal') NOT NULL COMMENT 'Tipo de local',
    capacidad_total    INT UNSIGNED NULL COMMENT 'Capacidad total de personas del local',
    activo             TINYINT(1)   DEFAULT 1 NOT NULL COMMENT 'Indica si el local está activo',
    fecha_apertura     DATE         NULL COMMENT 'Fecha de apertura del local',
    fecha_creacion     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP    DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)     NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)     NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT uq_local_codigo UNIQUE (codigo)
) COMMENT='Locales/restaurantes de la cadena';

CREATE INDEX idx_local_activo         ON local (activo);
CREATE INDEX idx_local_tipo           ON local (tipo_local);
CREATE INDEX idx_local_codigo         ON local (codigo);
CREATE INDEX idx_local_creado_por     ON local (creado_por);
CREATE INDEX idx_local_modificado_por ON local (modificado_por);


-- --------------------------------------------------------------------------
-- ZONA  
-- v1.1.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE zona (
    id                 CHAR(36)     NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_local           CHAR(36)     NOT NULL COMMENT 'ID del local al que pertenece la zona',
    nombre             VARCHAR(100) NOT NULL COMMENT 'Nombre de la zona (ej: Terraza, Interior, VIP)',
    descripcion        VARCHAR(200) NULL COMMENT 'Descripción detallada de la zona',
    nivel              INT          NOT NULL DEFAULT 0 COMMENT 'Nivel jerárquico (0=principal, 1=sub-zona, 2=sub-sub-zona)',
    capacidad_maxima   INT UNSIGNED NULL COMMENT 'Capacidad máxima de personas en la zona',
    activo             TINYINT(1)   DEFAULT 1 NOT NULL COMMENT 'Indica si la zona está activa',
    fecha_creacion     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP    DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)     NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)     NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT fk_zona_local
        FOREIGN KEY (id_local) REFERENCES local (id) ON DELETE CASCADE
) COMMENT='Zonas jerárquicas que organizan las mesas dentro de cada local';

CREATE INDEX idx_zona_local           ON zona (id_local);
CREATE INDEX idx_zona_activo          ON zona (activo);
CREATE INDEX idx_zona_nivel           ON zona (nivel);
CREATE INDEX idx_zona_creado_por      ON zona (creado_por);
CREATE INDEX idx_zona_modificado_por  ON zona (modificado_por);


-- --------------------------------------------------------------------------
-- SESION
-- v1.1.0 - Implementado en backend ✓  
-- --------------------------------------------------------------------------
CREATE TABLE sesion (
    id                 CHAR(36)                     NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_domotica        CHAR(36)                     NOT NULL COMMENT 'Identificador del sistema Domotica asociado',
    id_local           CHAR(36)                     NOT NULL COMMENT 'Identificador del local donde se registró la sesión',
    estado             ENUM('activo','inactivo','cerrado') DEFAULT 'activo' NOT NULL COMMENT 'Estado actual de la sesión',
    fecha_creacion     TIMESTAMP                    DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP                    DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)                     NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)                     NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT fk_sesion_local
        FOREIGN KEY (id_local) REFERENCES local (id) ON DELETE CASCADE
) COMMENT='Sesiones de sincronización entre el sistema Domotica y los locales';

CREATE INDEX idx_sesion_local         ON sesion (id_local);
CREATE INDEX idx_sesion_estado        ON sesion (estado);
CREATE INDEX idx_sesion_creado_por    ON sesion (creado_por);
CREATE INDEX idx_sesion_modificado_por ON sesion (modificado_por);


-- --------------------------------------------------------------------------
-- USUARIO (autorreferencia para auditoría)
-- v1.0.0 - Pendiente de implementación en backend
-- --------------------------------------------------------------------------
CREATE TABLE usuario (
    id                 CHAR(36)  NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_rol             CHAR(36)  NOT NULL,
    email              VARCHAR(255) NULL,
    password_hash      VARCHAR(255) NULL,
    nombre             VARCHAR(255) NULL,
    telefono           VARCHAR(20)  NULL,
    activo             TINYINT(1)   DEFAULT 1 NULL,
    ultimo_acceso      TIMESTAMP    NULL,
    fecha_creacion     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP    DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)     NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)     NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT uq_usuario_email UNIQUE (email),
    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (id_rol) REFERENCES rol (id)
) COMMENT='Usuarios del sistema (staff y clientes registrados)';

CREATE INDEX idx_usuario_activo         ON usuario (activo);
CREATE INDEX idx_usuario_email          ON usuario (email);
CREATE INDEX idx_usuario_rol            ON usuario (id_rol);
CREATE INDEX idx_usuario_creado_por     ON usuario (creado_por);
CREATE INDEX idx_usuario_modificado_por ON usuario (modificado_por); 

-- --------------------------------------------------------------------------
-- CATEGORIA
-- v1.0.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE categoria (
    id                 CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    nombre             VARCHAR(100)                           NOT NULL,
    descripcion        VARCHAR(200)                           NULL,
    activo             TINYINT(1)                             DEFAULT 1 NULL,
    imagen_path        VARCHAR(255)                           NULL,
    fecha_creacion     TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)                               NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)                               NULL COMMENT 'ID del usuario que modificó el registro (sin FK)'
) COMMENT='Categorías principales del menú';

CREATE INDEX idx_categoria_activo         ON categoria (activo);
CREATE INDEX idx_categoria_creado_por     ON categoria (creado_por);
CREATE INDEX idx_categoria_modificado_por ON categoria (modificado_por);

-- --------------------------------------------------------------------------
-- ALERGENO
-- v1.0.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE alergeno (
    id                 CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    nombre             VARCHAR(100)                           NOT NULL COMMENT 'Gluten, Lactosa, Mariscos, etc',
    descripcion        VARCHAR(200)                           NULL,
    icono              VARCHAR(50)                            NULL COMMENT 'Nombre del icono o emoji para UI',
    nivel_riesgo       ENUM ('bajo', 'medio', 'alto', 'critico') DEFAULT 'medio' NULL,
    activo             TINYINT(1)                             DEFAULT 1 NULL,
    fecha_creacion     TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)                               NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)                               NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT uq_alergeno_nombre UNIQUE (nombre)
) COMMENT='Catálogo de alérgenos alimentarios';

CREATE INDEX idx_alergeno_activo          ON alergeno (activo);
CREATE INDEX idx_alergeno_creado_por      ON alergeno (creado_por);
CREATE INDEX idx_alergeno_modificado_por  ON alergeno (modificado_por);

-- --------------------------------------------------------------------------
-- MESAS
-- v1.1.0 - Implementado en backend ✓ - Agregada relación con zona
-- --------------------------------------------------------------------------
CREATE TABLE mesas (
    id                 CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_zona            CHAR(36)                               NULL COMMENT 'ID de la zona donde se ubica la mesa',
    numero             VARCHAR(20)                            NOT NULL,
    capacidad          INT UNSIGNED                           NULL COMMENT 'Capacidad de personas',
    zona               VARCHAR(50)                            NULL COMMENT 'interior, terraza, vip, etc. (deprecated - usar id_zona)',
    nota               VARCHAR(255)                           NULL COMMENT 'Notas o comentarios adicionales sobre la mesa',
    estado             ENUM ('libre','disponible','ocupada','reservada','mantenimiento','fuera_servicio') DEFAULT 'disponible' NULL,
    activo             TINYINT(1)                             DEFAULT 1 NULL,
    fecha_creacion     TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)                               NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)                               NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT uq_mesa_numero UNIQUE (numero),
    CONSTRAINT fk_mesa_zona
        FOREIGN KEY (id_zona) REFERENCES zona (id) ON DELETE SET NULL
) COMMENT='Mesas físicas del restaurante';

CREATE INDEX idx_mesa_activo          ON mesas (activo);
CREATE INDEX idx_mesa_estado          ON mesas (estado);
CREATE INDEX idx_mesa_zona            ON mesas (zona);
CREATE INDEX idx_mesa_id_zona         ON mesas (id_zona);
CREATE INDEX idx_mesa_creado_por      ON mesas (creado_por);
CREATE INDEX idx_mesa_modificado_por  ON mesas (modificado_por);

-- --------------------------------------------------------------------------
-- PRODUCTO
-- v1.0.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE producto (
    id                 CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_categoria       CHAR(36)                               NOT NULL,
    nombre             VARCHAR(255)                           NOT NULL,
    descripcion        VARCHAR(200)                           NULL,
    precio_base        DECIMAL(10,2)                          NULL,
    imagen_path        VARCHAR(255)                           NULL,
    imagen_alt_text    VARCHAR(255)                           NULL,
    disponible         TINYINT(1)                             DEFAULT 1 NULL,
    destacado          TINYINT(1)                             DEFAULT 0 NULL,
    activo             TINYINT(1)                             DEFAULT 1 NULL,
    fecha_creacion     TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)                               NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)                               NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT fk_producto_categoria
        FOREIGN KEY (id_categoria) REFERENCES categoria (id),
    CONSTRAINT chk_producto_precio CHECK (precio_base > 0)
) COMMENT='Platos disponibles en el menú';

CREATE FULLTEXT INDEX idx_producto_busqueda   ON producto (nombre, descripcion);
CREATE INDEX idx_producto_categoria           ON producto (id_categoria);
CREATE INDEX idx_producto_destacado           ON producto (destacado);
CREATE INDEX idx_producto_disponible          ON producto (disponible);
CREATE INDEX idx_producto_activo              ON producto (activo);
CREATE INDEX idx_producto_precio              ON producto (precio_base);
CREATE INDEX idx_producto_creado_por          ON producto (creado_por);
CREATE INDEX idx_producto_modificado_por      ON producto (modificado_por);

-- --------------------------------------------------------------------------
-- TIPO_OPCION
-- v1.0.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE tipo_opcion (
    id                 CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    codigo             VARCHAR(50)                            NOT NULL COMMENT 'nivel_aji, acompanamiento, temperatura',
    nombre             VARCHAR(100)                           NOT NULL COMMENT 'Nivel de Ají, Acompañamiento, Temperatura',
    descripcion        VARCHAR(255)                           NULL,
    activo             TINYINT(1)                             DEFAULT 1 NULL,
    orden              INT UNSIGNED                           DEFAULT 0 NULL,
    seleccion_minima   INT UNSIGNED                           DEFAULT 0 NOT NULL COMMENT 'Cantidad mínima de opciones a seleccionar (0 = opcional)',
    seleccion_maxima   INT UNSIGNED                           NULL COMMENT 'Cantidad máxima de opciones (NULL = sin límite)',
    fecha_creacion     TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)                               NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)                               NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT uq_tipo_opcion_codigo UNIQUE (codigo)
);

CREATE INDEX idx_tipoop_activo            ON tipo_opcion (activo);
CREATE INDEX idx_tipoop_creado_por        ON tipo_opcion (creado_por);
CREATE INDEX idx_tipoop_modificado_por    ON tipo_opcion (modificado_por);

-- --------------------------------------------------------------------------
-- PRODUCTO_OPCION
-- v1.0.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE producto_opcion (
    id                 CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_producto        CHAR(36)                               NOT NULL,
    id_tipo_opcion     CHAR(36)                               NOT NULL,
    nombre             VARCHAR(100)                           NOT NULL COMMENT 'Sin ají, Ají suave, Con choclo, Helada',
    precio_adicional   DECIMAL(10,2)                          DEFAULT 0.00 NULL,
    activo             TINYINT(1)                             DEFAULT 1 NULL,
    orden              INT UNSIGNED                           DEFAULT 0 NULL,
    fecha_creacion     TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)                               NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)                               NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT fk_prodop_producto
        FOREIGN KEY (id_producto) REFERENCES producto (id) ON DELETE CASCADE,
    CONSTRAINT fk_prodop_tipo
        FOREIGN KEY (id_tipo_opcion) REFERENCES tipo_opcion (id)
);

CREATE INDEX idx_prodop_tipo           ON producto_opcion (id_tipo_opcion);
CREATE INDEX idx_prodop_prod_tipo      ON producto_opcion (id_producto, id_tipo_opcion);
CREATE INDEX idx_prodop_activo         ON producto_opcion (activo);
CREATE INDEX idx_prodop_creado_por     ON producto_opcion (creado_por);
CREATE INDEX idx_prodop_modificado_por ON producto_opcion (modificado_por);

-- --------------------------------------------------------------------------
-- PEDIDO
-- v1.1.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE pedido (
    id                   CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_mesa              CHAR(36)                               NOT NULL,
    numero_pedido        VARCHAR(50)                            NOT NULL,
    estado               ENUM ('pendiente','confirmado','en_preparacion','listo','entregado','cancelado') DEFAULT 'pendiente' NULL,
    subtotal             DECIMAL(10,2)                          NOT NULL DEFAULT 0.00,
    impuestos            DECIMAL(10,2)                          NULL     DEFAULT 0.00,
    descuentos           DECIMAL(10,2)                          NULL     DEFAULT 0.00,
    total                DECIMAL(10,2)                          NOT NULL DEFAULT 0.00,
    notas_cliente        VARCHAR(200)                           NULL,
    notas_cocina         VARCHAR(200)                           NULL,
    fecha_confirmado     TIMESTAMP                               NULL,
    fecha_en_preparacion TIMESTAMP                               NULL,
    fecha_listo          TIMESTAMP                               NULL,
    fecha_entregado      TIMESTAMP                               NULL,
    fecha_cancelado      TIMESTAMP                               NULL,
    fecha_creacion       TIMESTAMP                               DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion   TIMESTAMP                               DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por           CHAR(36)                                NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por       CHAR(36)                                NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT uq_pedido_numero UNIQUE (numero_pedido),
    CONSTRAINT fk_pedido_mesa
        FOREIGN KEY (id_mesa) REFERENCES mesas (id),
    CONSTRAINT chk_pedido_totales CHECK (subtotal >= 0 AND total >= 0)
) COMMENT='Pedidos/órdenes del restaurante';

CREATE INDEX idx_pedido_creado_por    ON pedido (creado_por);
CREATE INDEX idx_pedido_fecha_crea    ON pedido (fecha_creacion);
CREATE INDEX idx_pedido_estado        ON pedido (estado);
CREATE INDEX idx_pedido_mesa          ON pedido (id_mesa);
CREATE INDEX idx_pedido_numero        ON pedido (numero_pedido);
CREATE INDEX idx_pedido_modif_por     ON pedido (modificado_por);

-- --------------------------------------------------------------------------
-- PRODUCTO_ALERGENO (N:M)
-- v1.0.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE producto_alergeno (
    id_producto        CHAR(36)                               NOT NULL,
    id_alergeno        CHAR(36)                               NOT NULL,
    nivel_presencia    ENUM ('contiene','trazas','puede_contener') DEFAULT 'contiene' NULL,
    notas              VARCHAR(255)                           NULL COMMENT 'Información adicional sobre el alérgeno en este producto',
    activo             TINYINT(1)                             DEFAULT 1 NULL,
    fecha_creacion     TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)                               NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)                               NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    PRIMARY KEY (id_producto, id_alergeno),
    CONSTRAINT fk_prod_alerg_producto
        FOREIGN KEY (id_producto) REFERENCES producto (id) ON DELETE CASCADE,
    CONSTRAINT fk_prod_alerg_alergeno
        FOREIGN KEY (id_alergeno) REFERENCES alergeno (id)
) COMMENT='Alérgenos presentes en cada producto';

CREATE INDEX idx_prod_alerg_alergeno      ON producto_alergeno (id_alergeno);
CREATE INDEX idx_prod_alerg_producto      ON producto_alergeno (id_producto);
CREATE INDEX idx_prod_alerg_activo        ON producto_alergeno (activo);
CREATE INDEX idx_prod_alerg_creado_por    ON producto_alergeno (creado_por);
CREATE INDEX idx_prod_alerg_modificado_por ON producto_alergeno (modificado_por);

-- --------------------------------------------------------------------------
-- PEDIDO_PRODUCTO
-- v1.1.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE pedido_producto (
    id                   CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_pedido            CHAR(36)                               NOT NULL,
    id_producto          CHAR(36)                               NOT NULL,
    cantidad             INT                                    NOT NULL DEFAULT 1,
    precio_unitario      DECIMAL(10,2)                          NOT NULL COMMENT 'Precio base del producto',
    precio_opciones      DECIMAL(10,2)                          NOT NULL DEFAULT 0.00 COMMENT 'Suma de opciones adicionales',
    subtotal             DECIMAL(10,2)                          NOT NULL COMMENT 'cantidad * (precio_unitario + precio_opciones)',
    notas_personalizacion TEXT                                  NULL COMMENT 'Notas libres del cliente',
    fecha_creacion       TIMESTAMP                               NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion   TIMESTAMP                               NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_pedprod_pedido
        FOREIGN KEY (id_pedido) REFERENCES pedido (id) ON DELETE CASCADE,
    CONSTRAINT fk_pedprod_producto
        FOREIGN KEY (id_producto) REFERENCES producto (id) ON DELETE RESTRICT,
    CONSTRAINT chk_pedido_producto_cantidad_minima CHECK (cantidad >= 1),
    CONSTRAINT chk_pedido_producto_precio_unitario_positivo CHECK (precio_unitario > 0),
    CONSTRAINT chk_pedido_producto_precio_opciones_positivo CHECK (precio_opciones >= 0),
    CONSTRAINT chk_pedido_producto_subtotal_positivo CHECK (subtotal >= 0)
) COMMENT='Items/productos ordenados en cada pedido';

CREATE INDEX idx_pedprod_producto        ON pedido_producto (id_producto);
CREATE INDEX idx_pedprod_pedido          ON pedido_producto (id_pedido);

-- --------------------------------------------------------------------------
-- DIVISION_CUENTA
-- v1.1.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE division_cuenta (
    id                  CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_pedido           CHAR(36)                               NOT NULL,
    tipo_division       ENUM('equitativa','por_items','manual') NOT NULL,
    cantidad_personas   INT                                    NOT NULL,
    notas               TEXT                                   NULL,
    created_at          TIMESTAMP                               DEFAULT CURRENT_TIMESTAMP NULL,
    updated_at          TIMESTAMP                               DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_divcta_pedido
        FOREIGN KEY (id_pedido) REFERENCES pedido (id) ON DELETE CASCADE,
    CONSTRAINT chk_cantidad_personas CHECK (cantidad_personas > 0)
) COMMENT='Configuración de división de cuenta';

CREATE INDEX idx_divcta_pedido          ON division_cuenta (id_pedido);

-- --------------------------------------------------------------------------
-- DIVISION_CUENTA_DETALLE
-- v1.1.0 - Implementado en backend ✓
-- --------------------------------------------------------------------------
CREATE TABLE division_cuenta_detalle (
    id                  CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_division_cuenta  CHAR(36)                               NOT NULL,
    id_pedido_producto  CHAR(36)                               NOT NULL,
    persona_numero      INT                                    NOT NULL COMMENT 'Identificador de persona (1, 2, 3, etc)',
    monto_asignado      DECIMAL(10,2)                          NOT NULL COMMENT 'Monto que esta persona debe pagar por este item',
    created_at          TIMESTAMP                               DEFAULT CURRENT_TIMESTAMP NULL,
    CONSTRAINT fk_divdet_divcta
        FOREIGN KEY (id_division_cuenta) REFERENCES division_cuenta (id) ON DELETE CASCADE,
    CONSTRAINT fk_divdet_pedprod
        FOREIGN KEY (id_pedido_producto) REFERENCES pedido_producto (id) ON DELETE CASCADE,
    CONSTRAINT chk_monto_asignado CHECK (monto_asignado >= 0)
) COMMENT='Detalle de qué items paga cada persona';

CREATE INDEX idx_divdet_pedprod        ON division_cuenta_detalle (id_pedido_producto);
CREATE INDEX idx_divdet_division       ON division_cuenta_detalle (id_division_cuenta);
CREATE INDEX idx_divdet_persona        ON division_cuenta_detalle (persona_numero);

-- --------------------------------------------------------------------------
-- PEDIDO_OPCION
-- v1.0.0 - Pendiente de implementación en backend
-- --------------------------------------------------------------------------
CREATE TABLE pedido_opcion (
    id                 CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_pedido_producto CHAR(36)                               NOT NULL,
    id_producto_opcion CHAR(36)                               NOT NULL,
    precio_adicional   DECIMAL(10,2)                          DEFAULT 0.00 NULL COMMENT 'Precio al momento del pedido',
    fecha_creacion     TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL,
    creado_por         CHAR(36)                               NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)                               NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT fk_pedopc_pedprod
        FOREIGN KEY (id_pedido_producto) REFERENCES pedido_producto (id) ON DELETE CASCADE,
    CONSTRAINT fk_pedopc_prodop
        FOREIGN KEY (id_producto_opcion) REFERENCES producto_opcion (id)
) COMMENT='Opciones/personalizaciones aplicadas a cada item del pedido';

CREATE INDEX idx_pedopc_prodop         ON pedido_opcion (id_producto_opcion);
CREATE INDEX idx_pedopc_peditem        ON pedido_opcion (id_pedido_producto);
CREATE INDEX idx_pedopc_creado_por     ON pedido_opcion (creado_por);
CREATE INDEX idx_pedopc_modificado_por ON pedido_opcion (modificado_por);

-- --------------------------------------------------------------------------
-- PAGO
-- v1.0.0 - Pendiente de implementación en backend
-- --------------------------------------------------------------------------
CREATE TABLE pago (
    id                 CHAR(36)                               NOT NULL PRIMARY KEY COMMENT 'ULID/UUID - Identificador único',
    id_pedido          CHAR(36)                               NOT NULL,
    id_usuario         CHAR(36)                               NULL COMMENT 'NULL si es anónimo/efectivo',
    persona_numero     INT UNSIGNED                           NULL COMMENT 'Referencia a división_cuenta_detalle',
    metodo_pago        ENUM ('efectivo','tarjeta','yape','plin','transferencia') NOT NULL,
    monto              DECIMAL(10,2)                          NOT NULL,
    propina            DECIMAL(10,2)                          DEFAULT 0.00 NULL,
    total              DECIMAL(10,2)                          NOT NULL COMMENT 'monto + propina',
    estado             ENUM ('pendiente','procesando','completado','fallido','cancelado') DEFAULT 'pendiente' NULL,
    referencia_externa VARCHAR(255)                           NULL COMMENT 'ID de transacción de pasarela',
    notas              VARCHAR(200)                           NULL,
    fecha_procesado    TIMESTAMP                              NULL,
    fecha_completado   TIMESTAMP                              NULL,
    fecha_creacion     TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL,
    fecha_modificacion TIMESTAMP                              DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    creado_por         CHAR(36)                               NULL COMMENT 'ID del usuario que creó el registro (sin FK)',
    modificado_por     CHAR(36)                               NULL COMMENT 'ID del usuario que modificó el registro (sin FK)',
    CONSTRAINT fk_pago_pedido
        FOREIGN KEY (id_pedido) REFERENCES pedido (id),
    CONSTRAINT fk_pago_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuario (id) ON DELETE SET NULL,
    CONSTRAINT chk_pago_montos CHECK (monto >= 0 AND total >= 0)
) COMMENT='Pagos realizados por cada persona';

CREATE INDEX idx_pago_usuario        ON pago (id_usuario);
CREATE INDEX idx_pago_estado         ON pago (estado);
CREATE INDEX idx_pago_pedido         ON pago (id_pedido);
CREATE INDEX idx_pago_persona        ON pago (persona_numero);
CREATE INDEX idx_pago_creado_por     ON pago (creado_por);
CREATE INDEX idx_pago_modificado_por ON pago (modificado_por);
