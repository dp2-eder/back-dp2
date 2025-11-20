# Contrato de API - Gestión de Opciones de Productos

Este documento describe el contrato de las APIs para gestionar secciones de opciones y complementos de productos.

---

## Conceptos Clave

### Sección
Una **sección** es un tipo de opción que agrupa complementos relacionados. Ejemplos:
- "Extras" (agrupa complementos como "Queso Extra", "Aceitunas")
- "Nivel de Ají" (agrupa "Sin Ají", "Ají Suave", "Ají Picante")
- "Tamaño" (agrupa "Personal", "Mediana", "Familiar")

### Complemento
Un **complemento** es una opción específica dentro de una sección. Ejemplos:
- "Queso Extra" (complemento de la sección "Extras")
- "Ají Suave" (complemento de la sección "Nivel de Ají")

---

## 1. API: Listar Opciones de un Producto

### Endpoint
```
GET /api/v1/productos/{producto_id}/opciones-manage
```

### Descripción
Obtiene todas las secciones de opciones con sus complementos para un producto específico.

### Parámetros de URL

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `producto_id` | string (ULID) | Sí | ID único del producto |

### Headers Requeridos
```http
Content-Type: application/json
```

### Response Body (200 OK)

```typescript
{
  id_producto: string;              // ULID del producto
  nombre_producto: string;          // Nombre del producto
  total_secciones: number;          // Total de secciones del producto

  secciones: Array<{
    id_tipo_opcion: string;         // ULID del tipo de opción
    nombre: string;                 // Nombre de la sección (ej: "Extras")
    codigo: string;                 // Código interno (ej: "extras")
    descripcion: string | null;     // Descripción de la sección
    seleccion_minima: number;       // Mínimo a seleccionar
    seleccion_maxima: number | null;// Máximo a seleccionar (null = sin límite)
    orden: number | null;           // Orden de visualización
    activo: boolean;                // Si la sección está activa

    complementos: Array<{
      id: string;                   // ULID del complemento
      nombre: string;               // Nombre (ej: "Queso Extra")
      precio_adicional: string;     // Precio adicional (Decimal como string)
      activo: boolean;              // Si el complemento está activo
      orden: number;                // Orden de visualización
    }>;
  }>;
}
```

### Ejemplo de Response (200 OK)

```json
{
  "id_producto": "01KA9TRZE8PRODUCTO123",
  "nombre_producto": "Pizza Margherita",
  "total_secciones": 2,
  "secciones": [
    {
      "id_tipo_opcion": "01KA9TRZE8TAMANO123",
      "nombre": "Tamaño",
      "codigo": "tamano",
      "descripcion": "Seleccione el tamaño de la pizza",
      "seleccion_minima": 1,
      "seleccion_maxima": 1,
      "orden": 0,
      "activo": true,
      "complementos": [
        {
          "id": "01KAF7HZSYOPCION1",
          "nombre": "Personal (8 pulgadas)",
          "precio_adicional": "0.00",
          "activo": true,
          "orden": 0
        },
        {
          "id": "01KAF7HZSYOPCION2",
          "nombre": "Mediana (12 pulgadas)",
          "precio_adicional": "5.00",
          "activo": true,
          "orden": 1
        },
        {
          "id": "01KAF7HZSYOPCION3",
          "nombre": "Familiar (16 pulgadas)",
          "precio_adicional": "10.00",
          "activo": true,
          "orden": 2
        }
      ]
    },
    {
      "id_tipo_opcion": "01KA9TRZE8EXTRAS456",
      "nombre": "Extras",
      "codigo": "extras",
      "descripcion": "Ingredientes adicionales",
      "seleccion_minima": 0,
      "seleccion_maxima": 5,
      "orden": 1,
      "activo": true,
      "complementos": [
        {
          "id": "01KAF7HZSYOPCION4",
          "nombre": "Queso Extra",
          "precio_adicional": "2.50",
          "activo": true,
          "orden": 0
        },
        {
          "id": "01KAF7HZSYOPCION5",
          "nombre": "Aceitunas",
          "precio_adicional": "1.50",
          "activo": true,
          "orden": 1
        },
        {
          "id": "01KAF7HZSYOPCION6",
          "nombre": "Champiñones",
          "precio_adicional": "2.00",
          "activo": true,
          "orden": 2
        }
      ]
    }
  ]
}
```

### Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| `200 OK` | Opciones obtenidas exitosamente |
| `404 Not Found` | Producto no encontrado |
| `500 Internal Server Error` | Error interno del servidor |

---

## 2. API: Agregar Opciones a un Producto

### Endpoint
```
POST /api/v1/productos/{producto_id}/opciones-manage
```

### Descripción
Agrega una o más secciones (tipos de opciones) con sus complementos a un producto.

### ⚠️ Comportamiento Importante

| Concepto | Comportamiento |
|----------|----------------|
| **Sección existente** | Si una sección con el mismo nombre ya existe, se **reutiliza** |
| **Sección nueva** | Si no existe, se **crea automáticamente** |
| **Código de sección** | Se genera automáticamente a partir del nombre (ej: "Nivel de Ají" → "nivel_de_aji") |
| **Complementos** | Siempre se **crean nuevos** para el producto específico |

### Parámetros de URL

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `producto_id` | string (ULID) | Sí | ID único del producto |

### Headers Requeridos
```http
Content-Type: application/json
```

### Request Body

```typescript
{
  secciones: Array<{
    nombre_seccion: string;         // REQUERIDO. Nombre de la sección (ej: "Extras", "Nivel de Ají")
    descripcion: string | null;     // OPCIONAL. Descripción de la sección
    seleccion_minima: number;       // REQUERIDO. Mínimo a seleccionar (0 = opcional)
    seleccion_maxima: number | null;// OPCIONAL. Máximo a seleccionar (null = sin límite)

    complementos: Array<{           // REQUERIDO. Mínimo 1 complemento
      nombre: string;               // REQUERIDO. Nombre del complemento
      precio_adicional: string | number;  // REQUERIDO. Precio adicional (puede ser 0)
      orden: number | null;         // OPCIONAL. Orden de visualización (default: índice en array)
    }>;
  }>;
}
```

### Validaciones

| Campo | Validación |
|-------|-----------|
| `nombre_seccion` | Mínimo 1 carácter, máximo 100 |
| `descripcion` | Máximo 255 caracteres |
| `seleccion_minima` | Mayor o igual a 0 |
| `seleccion_maxima` | Mayor o igual a 1 (o null para sin límite) |
| `complementos` | Array con mínimo 1 elemento |
| `nombre` (complemento) | Mínimo 1 carácter, máximo 100 |
| `precio_adicional` | Mayor o igual a 0 |

### Ejemplo de Request - Una Sección Simple

```json
{
  "secciones": [
    {
      "nombre_seccion": "Extras",
      "descripcion": "Ingredientes adicionales",
      "seleccion_minima": 0,
      "seleccion_maxima": 5,
      "complementos": [
        {
          "nombre": "Queso Extra",
          "precio_adicional": "2.50"
        },
        {
          "nombre": "Aceitunas",
          "precio_adicional": "1.50"
        }
      ]
    }
  ]
}
```

### Ejemplo de Request - Múltiples Secciones

```json
{
  "secciones": [
    {
      "nombre_seccion": "Tamaño",
      "descripcion": "Seleccione el tamaño",
      "seleccion_minima": 1,
      "seleccion_maxima": 1,
      "complementos": [
        {
          "nombre": "Personal (8 pulgadas)",
          "precio_adicional": "0.00",
          "orden": 0
        },
        {
          "nombre": "Mediana (12 pulgadas)",
          "precio_adicional": "5.00",
          "orden": 1
        },
        {
          "nombre": "Familiar (16 pulgadas)",
          "precio_adicional": "10.00",
          "orden": 2
        }
      ]
    },
    {
      "nombre_seccion": "Nivel de Ají",
      "descripcion": "Seleccione el nivel de picante",
      "seleccion_minima": 1,
      "seleccion_maxima": 1,
      "complementos": [
        {
          "nombre": "Sin Ají",
          "precio_adicional": "0.00",
          "orden": 0
        },
        {
          "nombre": "Ají Suave",
          "precio_adicional": "0.00",
          "orden": 1
        },
        {
          "nombre": "Ají Picante",
          "precio_adicional": "0.50",
          "orden": 2
        }
      ]
    },
    {
      "nombre_seccion": "Extras",
      "descripcion": "Ingredientes adicionales",
      "seleccion_minima": 0,
      "seleccion_maxima": null,
      "complementos": [
        {
          "nombre": "Queso Extra",
          "precio_adicional": "2.50"
        },
        {
          "nombre": "Champiñones",
          "precio_adicional": "2.00"
        },
        {
          "nombre": "Aceitunas",
          "precio_adicional": "1.50"
        },
        {
          "nombre": "Tocino",
          "precio_adicional": "3.00"
        }
      ]
    }
  ]
}
```

### Response Body (201 CREATED)

```typescript
{
  mensaje: string;                  // Mensaje de confirmación
  secciones_creadas: number;        // Número de secciones creadas/reutilizadas
  complementos_creados: number;     // Número total de complementos creados

  detalles: Array<{
    id_tipo_opcion: string;
    nombre: string;
    codigo: string;
    descripcion: string | null;
    seleccion_minima: number;
    seleccion_maxima: number | null;
    orden: number | null;
    activo: boolean;

    complementos: Array<{
      id: string;
      nombre: string;
      precio_adicional: string;
      activo: boolean;
      orden: number;
    }>;
  }>;
}
```

### Ejemplo de Response (201 CREATED)

```json
{
  "mensaje": "Se agregaron 3 sección(es) con 10 complemento(s) al producto",
  "secciones_creadas": 3,
  "complementos_creados": 10,
  "detalles": [
    {
      "id_tipo_opcion": "01KA9TRZE8TAMANO123",
      "nombre": "Tamaño",
      "codigo": "tamano",
      "descripcion": "Seleccione el tamaño",
      "seleccion_minima": 1,
      "seleccion_maxima": 1,
      "orden": 0,
      "activo": true,
      "complementos": [
        {
          "id": "01KAF7HZSYCOMP1",
          "nombre": "Personal (8 pulgadas)",
          "precio_adicional": "0.00",
          "activo": true,
          "orden": 0
        },
        {
          "id": "01KAF7HZSYCOMP2",
          "nombre": "Mediana (12 pulgadas)",
          "precio_adicional": "5.00",
          "activo": true,
          "orden": 1
        },
        {
          "id": "01KAF7HZSYCOMP3",
          "nombre": "Familiar (16 pulgadas)",
          "precio_adicional": "10.00",
          "activo": true,
          "orden": 2
        }
      ]
    },
    {
      "id_tipo_opcion": "01KA9TRZE8NIVELAJI456",
      "nombre": "Nivel de Ají",
      "codigo": "nivel_de_aji",
      "descripcion": "Seleccione el nivel de picante",
      "seleccion_minima": 1,
      "seleccion_maxima": 1,
      "orden": 0,
      "activo": true,
      "complementos": [
        {
          "id": "01KAF7HZSYCOMP4",
          "nombre": "Sin Ají",
          "precio_adicional": "0.00",
          "activo": true,
          "orden": 0
        },
        {
          "id": "01KAF7HZSYCOMP5",
          "nombre": "Ají Suave",
          "precio_adicional": "0.00",
          "activo": true,
          "orden": 1
        },
        {
          "id": "01KAF7HZSYCOMP6",
          "nombre": "Ají Picante",
          "precio_adicional": "0.50",
          "activo": true,
          "orden": 2
        }
      ]
    },
    {
      "id_tipo_opcion": "01KA9TRZE8EXTRAS789",
      "nombre": "Extras",
      "codigo": "extras",
      "descripcion": "Ingredientes adicionales",
      "seleccion_minima": 0,
      "seleccion_maxima": null,
      "orden": 0,
      "activo": true,
      "complementos": [
        {
          "id": "01KAF7HZSYCOMP7",
          "nombre": "Queso Extra",
          "precio_adicional": "2.50",
          "activo": true,
          "orden": 0
        },
        {
          "id": "01KAF7HZSYCOMP8",
          "nombre": "Champiñones",
          "precio_adicional": "2.00",
          "activo": true,
          "orden": 1
        },
        {
          "id": "01KAF7HZSYCOMP9",
          "nombre": "Aceitunas",
          "precio_adicional": "1.50",
          "activo": true,
          "orden": 2
        },
        {
          "id": "01KAF7HZSYCOMP10",
          "nombre": "Tocino",
          "precio_adicional": "3.00",
          "activo": true,
          "orden": 3
        }
      ]
    }
  ]
}
```

### Códigos de Estado HTTP

| Código | Descripción | Ejemplo de Error |
|--------|-------------|------------------|
| `201 CREATED` | Secciones y complementos creados exitosamente | - |
| `400 Bad Request` | Datos de entrada inválidos | Campos requeridos faltantes, array de complementos vacío |
| `404 Not Found` | Producto no encontrado | El `producto_id` no existe |
| `422 Unprocessable Entity` | Error de validación de Pydantic | Tipo de dato incorrecto, valores fuera de rango |
| `500 Internal Server Error` | Error interno del servidor | Error de base de datos |

### Ejemplo de Error (404 Not Found)

```json
{
  "detail": "Producto con ID '01KA9TRZE8INVALID123' no encontrado"
}
```

### Ejemplo de Error (422 Unprocessable Entity)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "secciones", 0, "nombre_seccion"],
      "msg": "Field required",
      "input": {...}
    },
    {
      "type": "too_short",
      "loc": ["body", "secciones", 0, "complementos"],
      "msg": "List should have at least 1 item after validation, not 0",
      "input": []
    }
  ]
}
```

---

## Casos de Uso

### Caso 1: Producto Nuevo sin Opciones

**Situación**: Una pizza nueva sin opciones configuradas.

**Acción**: Agregar secciones de Tamaño y Extras.

```javascript
const response = await fetch('/api/v1/productos/01KA9TRZE8PIZZA123/opciones-manage', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    secciones: [
      {
        nombre_seccion: "Tamaño",
        seleccion_minima: 1,
        seleccion_maxima: 1,
        complementos: [
          { nombre: "Personal", precio_adicional: "0.00" },
          { nombre: "Mediana", precio_adicional: "5.00" },
          { nombre: "Familiar", precio_adicional: "10.00" }
        ]
      }
    ]
  })
});
```

---

### Caso 2: Producto con Opciones Existentes

**Situación**: Un producto ya tiene la sección "Tamaño", quiero agregar "Extras".

**Acción**: Agregar solo la sección "Extras".

```javascript
const response = await fetch('/api/v1/productos/01KA9TRZE8PIZZA123/opciones-manage', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    secciones: [
      {
        nombre_seccion: "Extras",
        seleccion_minima: 0,
        seleccion_maxima: null,
        complementos: [
          { nombre: "Queso Extra", precio_adicional: "2.50" },
          { nombre: "Aceitunas", precio_adicional: "1.50" }
        ]
      }
    ]
  })
});
```

---

### Caso 3: Consultar Opciones de un Producto

**Situación**: Mostrar en el frontend las opciones configuradas.

**Acción**: Listar opciones del producto.

```javascript
const response = await fetch('/api/v1/productos/01KA9TRZE8PIZZA123/opciones-manage');
const data = await response.json();

console.log(`Producto: ${data.nombre_producto}`);
console.log(`Total secciones: ${data.total_secciones}`);

data.secciones.forEach(seccion => {
  console.log(`\nSección: ${seccion.nombre}`);
  console.log(`  Rango: ${seccion.seleccion_minima} - ${seccion.seleccion_maxima || 'Sin límite'}`);

  seccion.complementos.forEach(comp => {
    console.log(`  - ${comp.nombre}: +$${comp.precio_adicional}`);
  });
});
```

---

## Integración Frontend

### React + TypeScript - Ejemplo Completo

```typescript
import { useState } from 'react';
import { Decimal } from 'decimal.js';

interface Complemento {
  nombre: string;
  precio_adicional: string;
  orden?: number;
}

interface Seccion {
  nombre_seccion: string;
  descripcion?: string;
  seleccion_minima: number;
  seleccion_maxima: number | null;
  complementos: Complemento[];
}

interface AgregarOpcionesRequest {
  secciones: Seccion[];
}

function FormularioOpcionesProducto({ productoId }: { productoId: string }) {
  const [nombreSeccion, setNombreSeccion] = useState('');
  const [complementos, setComplementos] = useState<Complemento[]>([
    { nombre: '', precio_adicional: '0.00' }
  ]);

  const agregarComplemento = () => {
    setComplementos([...complementos, { nombre: '', precio_adicional: '0.00' }]);
  };

  const actualizarComplemento = (index: number, campo: keyof Complemento, valor: string) => {
    const nuevosComplementos = [...complementos];
    nuevosComplementos[index] = { ...nuevosComplementos[index], [campo]: valor };
    setComplementos(nuevosComplementos);
  };

  const enviarFormulario = async () => {
    const request: AgregarOpcionesRequest = {
      secciones: [
        {
          nombre_seccion: nombreSeccion,
          descripcion: null,
          seleccion_minima: 0,
          seleccion_maxima: null,
          complementos: complementos.map((comp, idx) => ({
            nombre: comp.nombre,
            precio_adicional: comp.precio_adicional,
            orden: idx
          }))
        }
      ]
    };

    try {
      const response = await fetch(`/api/v1/productos/${productoId}/opciones-manage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error('Error al agregar opciones');
      }

      const resultado = await response.json();
      alert(`Se agregó la sección con ${resultado.complementos_creados} complementos`);

      // Limpiar formulario
      setNombreSeccion('');
      setComplementos([{ nombre: '', precio_adicional: '0.00' }]);

    } catch (error) {
      console.error('Error:', error);
      alert('Error al agregar opciones al producto');
    }
  };

  return (
    <div>
      <h3>Agregar Sección de Opciones</h3>

      <div>
        <label>Nombre de la Sección:</label>
        <input
          type="text"
          value={nombreSeccion}
          onChange={(e) => setNombreSeccion(e.target.value)}
          placeholder="Ej: Extras, Nivel de Ají"
        />
      </div>

      <h4>Complementos</h4>
      {complementos.map((comp, index) => (
        <div key={index}>
          <input
            type="text"
            value={comp.nombre}
            onChange={(e) => actualizarComplemento(index, 'nombre', e.target.value)}
            placeholder="Nombre del complemento"
          />
          <input
            type="number"
            step="0.01"
            min="0"
            value={comp.precio_adicional}
            onChange={(e) => actualizarComplemento(index, 'precio_adicional', e.target.value)}
            placeholder="Precio adicional"
          />
        </div>
      ))}

      <button onClick={agregarComplemento}>+ Agregar Complemento</button>
      <button onClick={enviarFormulario}>Guardar Sección</button>
    </div>
  );
}
```

---

## Notas Importantes

### 1. Reutilización de Secciones

Las secciones (tipos de opciones) se reutilizan automáticamente si ya existen:

```
Producto A tiene "Extras" → Código: "extras"
Producto B agrega "Extras" → Reutiliza el mismo tipo de opción
```

**Beneficio**: Consistencia en todo el sistema.

### 2. Generación de Códigos

Los códigos se generan automáticamente:

| Nombre de Sección | Código Generado |
|-------------------|-----------------|
| "Extras" | "extras" |
| "Nivel de Ají" | "nivel_de_aji" |
| "Tamaño" | "tamano" |
| "Ingredientes Adicionales" | "ingredientes_adicionales" |

### 3. Precios Adicionales

Los precios adicionales se suman al precio base del producto:

```
Producto Base: $15.00
+ Tamaño Familiar: +$10.00
+ Queso Extra: +$2.50
----------------------------
Total: $27.50
```

### 4. Ordenamiento

El orden de visualización se puede especificar:
- Si no se proporciona `orden`, se usa el índice del array
- Las secciones y complementos se ordenan por el campo `orden`

---

## Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | 2025-01-19 | Versión inicial del contrato de API para gestión de opciones |

---

**Contacto de Soporte**: Para dudas o problemas, contactar al equipo de backend.
