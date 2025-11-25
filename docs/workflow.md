# Workflow de Desarrollo Backend

Este documento describe el proceso de trabajo recomendado para el desarrollo del backend, con énfasis en la integración con Front-end y UI/UX, así como en las prácticas de testing y control de calidad.

## 1. Flujo de Trabajo General

### 1.1 Mapeo de Necesidades UI/UX y Front-end

1. **Reunión de Planificación**:
   - Analizar los wireframes, mockups y diseños provistos por el equipo de UI/UX.
   - Identificar las interacciones y flujos de datos necesarios desde el Front-end.
   - Documentar los requerimientos funcionales en historias de usuario.

2. **Definición de Endpoints**:
   - Crear un documento de especificación de API para cada flujo.
   - Definir claramente para cada endpoint:
     - Método HTTP (GET, POST, PUT, DELETE, etc.)
     - Ruta
     - Parámetros esperados
     - Cuerpo de la solicitud (request body)
     - Respuestas esperadas (códigos HTTP y estructuras JSON)
     - Validaciones necesarias
   - Compartir y validar esta especificación con el equipo de Front-end.

### 1.2 Desarrollo Incremental

Para cada funcionalidad, seguir este orden de desarrollo:

1. **Modelo (Model)**
2. **Repositorio (Repository)**
3. **Servicio (Service)**
4. **Controlador (Controller)**

Cada fase incluye su propio ciclo de desarrollo y pruebas antes de pasar a la siguiente.

## 2. Desarrollo por Capas

### 2.1 Capa de Modelo

#### 2.1.1 Desarrollo
- Definir la estructura de datos según los requisitos.
- Implementar el modelo con SQLAlchemy siguiendo los estándares del proyecto.
- Incluir anotaciones de tipo utilizando type hints de Python.
- Documentar cada atributo siguiendo el formato de docstrings establecido.

#### 2.1.2 Testing
- Implementar pruebas unitarias que verifiquen:
  - Creación correcta del modelo
  - Valores por defecto
  - Comportamiento de propiedades y métodos

#### 2.1.3 PR (Pull Request)
- Crear un PR específico para el modelo y sus pruebas.
- Asegurar una cobertura de pruebas cercana al 100% para esta capa.

### 2.2 Capa de Repositorio

#### 2.2.1 Desarrollo
- Implementar el repositorio con los métodos CRUD básicos.
- Añadir métodos específicos para consultas complejas.
- Documentar cada método siguiendo el formato establecido.

#### 2.2.2 Testing
- **Pruebas unitarias**:
  - Mocks de la sesión de base de datos.
  - Verificación de que se construyen y ejecutan las consultas correctamente.

- **Pruebas de integración**:
  - Configurar una base de datos en memoria o contenedor de prueba.
  - Verificar interacción real con la base de datos.

#### 2.2.3 PR
- Crear un PR específico para el repositorio y sus pruebas.
- Referenciar el PR del modelo relacionado.

### 2.3 Capa de Servicio (Lógica de Negocio)

#### 2.3.1 Desarrollo
- Implementar la lógica de negocio utilizando los repositorios.
- Manejar validaciones complejas y reglas de negocio.
- Implementar manejo de excepciones específicas.
- Documentar cada método según formato establecido.

#### 2.3.2 Testing
- **Pruebas unitarias**:
  - Mocks de los repositorios dependientes.
  - Verificación de la lógica de negocio en diferentes escenarios.
  - Casos de éxito y casos de error.

- **Pruebas de integración**:
  - Verificar interacción entre servicio y repositorio real.

#### 2.3.3 PR
- Crear un PR específico para el servicio y sus pruebas.
- Referenciar los PRs de modelo y repositorio relacionados.

### 2.4 Capa de Controlador (API)

#### 2.4.1 Desarrollo
- Implementar los endpoints definidos utilizando FastAPI.
- Configurar las dependencias para inyectar los servicios necesarios.
- Definir esquemas de request/response con Pydantic.
- Implementar documentación de API con OpenAPI/Swagger.
- Documentar cada endpoint según formato establecido.

#### 2.4.2 Testing
- **Pruebas unitarias**:
  - Mocks de los servicios dependientes.
  - Verificación de códigos HTTP correctos.
  - Validación de respuestas según esquemas definidos.

- **Pruebas de integración**:
  - Verificar flujo completo desde el controlador hasta la base de datos.

#### 2.4.3 PR
- Crear un PR específico para el controlador y sus pruebas.
- Referenciar los PRs de modelo, repositorio y servicio relacionados.

## 3. Buenas Prácticas

### 3.1 Estructura de Docstrings

Seguir la estructura definida en `docstring.md`, asegurándose de documentar:
- Propósito de cada clase/método/función
- Parámetros con tipos
- Valores de retorno
- Excepciones lanzadas

### 3.2 Testing

- Seguir la estructura de docstrings para pruebas definida en `testing.md`:
  ```python
  """
  Descripción breve.

  PRECONDICIONES:
      - Requisitos previos.

  PROCESO:
      - Pasos de la prueba.

  POSTCONDICIONES:
      - Resultados esperados.
  """
  ```

- Ejecutar análisis de cobertura regularmente:
  ```bash
  pytest --cov=src --cov-report=term-missing
  ```

- Objetivo: mantener una cobertura de pruebas > 80% para código de producción.

### 3.3 Control de Versiones

- **Ramas**:
  - `main`: producción/estable
  - `qa`: control de calidad
  - `dev`: integración de nuevas características
  - `feat/nombre-funcionalidad`: nombre en minusculas separada por guiones para nuevas funcionalidades
  - `fix/nombre-bug`: para correcciones de bugs
  - `hotfix/nombre-bug`: cambios MUY URGENTES directos a main

- **Commits**:
  - Mensajes descriptivos y concisos
  - Formato recomendado: `[Tipo] Descripción corta`
  - Tipos: `upd`, `feat`, `fix`, `docs`, `test`, `refactor`

- **Pull Requests**:
  - PRs pequeños y enfocados (una capa a la vez)
  - Incluir pruebas relevantes
  - Referenciar issues/tickets relacionados
  - Asegurar que pasa CI antes de solicitar revisión

### 3.4 Revisión de Código

- Lista de verificación para revisiones:
  - Sigue las convenciones de estilo del proyecto
  - Tiene documentación adecuada
  - Incluye pruebas suficientes
  - No introduce código duplicado
  - Maneja errores apropiadamente

### 3.5 Type Checking

- Utilizar type hints en todo el código nuevo.
- Configurar su editor de codigo para eso.

### 3.6 Consultas y Recursos

1. **Orden de consulta**:
   - Documentación oficial de la librería (FastAPI, SQLAlchemy, etc.)
   - Ejemplos de código en el proyecto actual
   - Stack Overflow/Foros específicos
   - Asistentes IA (como último recurso)

2. **Recursos recomendados**:
   - [Documentación de FastAPI](https://fastapi.tiangolo.com/)
   - [Documentación de SQLAlchemy](https://docs.sqlalchemy.org/)
   - [Documentación de Pydantic](https://docs.pydantic.dev/)
   - [Documentación de pytest](https://docs.pytest.org/)

## 4. Monitoreo de Calidad

### 4.1 CI/CD

- Pipeline que ejecuta automáticamente:
  - Linting (flake8, black)
  - Type checking (mypy)
  - Tests unitarios e integración (pytest)
  - Análisis de cobertura (pytest-cov)

### 4.2 Revisión de Métricas

- Revisar regularmente:
  - Cobertura de código
  - Complejidad ciclomática
  - Duplicación de código
  - Deuda técnica

## 5. Ejemplo de Workflow Completo

### Ejemplo: Funcionalidad "Gestión de Productos"

1. **Planificación**:
   - Revisar mockups de UI/UX para la gestión de productos
   - Definir endpoints necesarios: CRUD de productos

2. **Modelo (PR #1)**:
   ```python
   # src/models/menu/producto_model.py
   class ProductoModel(BaseModel):
       """Modelo que representa un producto del menú."""
       # Implementación

   # tests/unit/models/menu/test_producto_model.py
   def test_producto_model_creation():
       """
       Verifica que un objeto ProductoModel se crea correctamente.

       PRECONDICIONES:
           - Ninguna especial.

       PROCESO:
           - Crear instancia con valores específicos.

       POSTCONDICIONES:
           - Los atributos deben tener los valores correctos.
       """
       # Implementación del test
   ```

3. **Repositorio (PR #2)**:
   ```python
   # src/repositories/menu/producto_repository.py
   class ProductoRepository:
       """Repositorio para operaciones CRUD de productos."""
       # Implementación

   # tests/unit/repositories/menu/test_producto_repository.py y tests de integración
   # Implementación de tests unitarios con mocks

   # tests/integration/repositories/menu/test_producto_repository_integration.py
   # Implementación de tests de integración con BD real
   ```

4. **Servicio (PR #3)**:
   ```python
   # src/business_logic/menu/producto_service.py
   class ProductoService:
       """Servicio para la gestión de productos."""
       # Implementación

   # tests unitarios y de integración correspondientes
   ```

5. **Controlador (PR #4)**:
   ```python
   # src/api/controllers/productos_controller.py
   @router.get("/productos", response_model=List[ProductoResponse])
   async def get_productos(...):
       """
       Obtiene la lista de productos.

       [Documentación completa]
       """
       # Implementación

   # tests unitarios y de integración correspondientes
   ```
