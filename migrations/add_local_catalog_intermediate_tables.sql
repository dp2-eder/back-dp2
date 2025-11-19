-- Migration: Add Local Catalog Intermediate Tables
-- Description: Creates 4 new intermediate tables to support multi-local catalog system
-- Date: 2025-11-01
-- Author: System

-- =============================================================================
-- 1. locales_categorias
--    Relación entre Local y Categoría (activación por local)
-- =============================================================================

CREATE TABLE IF NOT EXISTS locales_categorias (
    id VARCHAR(26) PRIMARY KEY COMMENT 'ULID único',
    id_local VARCHAR(26) NOT NULL COMMENT 'Identificador del local',
    id_categoria VARCHAR(26) NOT NULL COMMENT 'Identificador de la categoría',
    activo BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Indica si la categoría está activa en este local',
    orden_override INT NULL COMMENT 'Orden personalizado para este local (NULL = usar orden original)',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación',
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Fecha de última modificación',

    -- Foreign Keys
    CONSTRAINT fk_locales_categorias_local
        FOREIGN KEY (id_local) REFERENCES locales(id) ON DELETE CASCADE,
    CONSTRAINT fk_locales_categorias_categoria
        FOREIGN KEY (id_categoria) REFERENCES categorias(id) ON DELETE CASCADE,

    -- Unique Constraint
    CONSTRAINT uq_locales_categorias
        UNIQUE (id_local, id_categoria),

    -- Indexes
    INDEX idx_locales_categorias_activo (id_local, activo),
    INDEX idx_locales_categorias_categoria (id_categoria)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Relación entre Local y Categoría con activación por local';


-- =============================================================================
-- 2. locales_productos
--    Relación entre Local y Producto con campos de override
-- =============================================================================

CREATE TABLE IF NOT EXISTS locales_productos (
    id VARCHAR(26) PRIMARY KEY COMMENT 'ULID único',
    id_local VARCHAR(26) NOT NULL COMMENT 'Identificador del local',
    id_producto VARCHAR(26) NOT NULL COMMENT 'Identificador del producto',
    activo BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Indica si el producto está activo en este local',

    -- Override fields (NULL = usar valor original)
    precio_override DECIMAL(10, 2) NULL COMMENT 'Precio personalizado para este local',
    disponible_override BOOLEAN NULL COMMENT 'Disponibilidad personalizada',
    nombre_override VARCHAR(100) NULL COMMENT 'Nombre personalizado para este local',
    descripcion_override VARCHAR(500) NULL COMMENT 'Descripción personalizada para este local',

    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación',
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Fecha de última modificación',

    -- Foreign Keys
    CONSTRAINT fk_locales_productos_local
        FOREIGN KEY (id_local) REFERENCES locales(id) ON DELETE CASCADE,
    CONSTRAINT fk_locales_productos_producto
        FOREIGN KEY (id_producto) REFERENCES productos(id) ON DELETE CASCADE,

    -- Unique Constraint
    CONSTRAINT uq_locales_productos
        UNIQUE (id_local, id_producto),

    -- Indexes
    INDEX idx_locales_productos_activo (id_local, activo),
    INDEX idx_locales_productos_producto (id_producto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Relación entre Local y Producto con overrides opcionales';


-- =============================================================================
-- 3. locales_tipos_opciones
--    Relación entre Local y TipoOpcion (activación por local)
-- =============================================================================

CREATE TABLE IF NOT EXISTS locales_tipos_opciones (
    id VARCHAR(26) PRIMARY KEY COMMENT 'ULID único',
    id_local VARCHAR(26) NOT NULL COMMENT 'Identificador del local',
    id_tipo_opcion VARCHAR(26) NOT NULL COMMENT 'Identificador del tipo de opción',
    activo BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Indica si el tipo de opción está activo en este local',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación',
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Fecha de última modificación',

    -- Foreign Keys
    CONSTRAINT fk_locales_tipos_opciones_local
        FOREIGN KEY (id_local) REFERENCES locales(id) ON DELETE CASCADE,
    CONSTRAINT fk_locales_tipos_opciones_tipo
        FOREIGN KEY (id_tipo_opcion) REFERENCES tipos_opciones(id) ON DELETE CASCADE,

    -- Unique Constraint
    CONSTRAINT uq_locales_tipos_opciones
        UNIQUE (id_local, id_tipo_opcion),

    -- Indexes
    INDEX idx_locales_tipos_opciones_activo (id_local, activo),
    INDEX idx_locales_tipos_opciones_tipo (id_tipo_opcion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Relación entre Local y TipoOpcion con activación por local';


-- =============================================================================
-- 4. locales_productos_opciones
--    Relación entre Local y ProductoOpcion con override de precio
-- =============================================================================

CREATE TABLE IF NOT EXISTS locales_productos_opciones (
    id VARCHAR(26) PRIMARY KEY COMMENT 'ULID único',
    id_local VARCHAR(26) NOT NULL COMMENT 'Identificador del local',
    id_producto_opcion VARCHAR(26) NOT NULL COMMENT 'Identificador de la opción de producto',
    activo BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Indica si la opción está activa en este local',

    -- Override field (NULL = usar valor original)
    precio_adicional_override DECIMAL(10, 2) NULL COMMENT 'Precio adicional personalizado para este local',

    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación',
    fecha_modificacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Fecha de última modificación',

    -- Foreign Keys
    CONSTRAINT fk_locales_productos_opciones_local
        FOREIGN KEY (id_local) REFERENCES locales(id) ON DELETE CASCADE,
    CONSTRAINT fk_locales_productos_opciones_opcion
        FOREIGN KEY (id_producto_opcion) REFERENCES productos_opciones(id) ON DELETE CASCADE,

    -- Unique Constraint
    CONSTRAINT uq_locales_productos_opciones
        UNIQUE (id_local, id_producto_opcion),

    -- Indexes
    INDEX idx_locales_productos_opciones_activo (id_local, activo),
    INDEX idx_locales_productos_opciones_opcion (id_producto_opcion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Relación entre Local y ProductoOpcion con override de precio adicional';


-- =============================================================================
-- ROLLBACK SCRIPT (if needed)
-- =============================================================================

-- To rollback this migration, run:
-- DROP TABLE IF EXISTS locales_productos_opciones;
-- DROP TABLE IF EXISTS locales_tipos_opciones;
-- DROP TABLE IF EXISTS locales_productos;
-- DROP TABLE IF EXISTS locales_categorias;
