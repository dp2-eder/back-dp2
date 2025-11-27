 FORMATO ESTÁNDAR - EQUIPO QA

  1. TÍTULO DEL ISSUE

  Casos de Prueba - [CÓDIGO]: [Nombre descriptivo]

  Ejemplos:
  - Casos de Prueba - HU-C07: Añadir extras disponibles
  - Casos de Prueba - CU-01: Crear Pedido Completo Simple

  ---
  2. ETIQUETAS (LABELS)

  Usar DOS etiquetas obligatorias:
  - QA (para identificar que es del área de QA)
  - testing o bug (según el tipo de issue)

  ### Cuándo usar cada etiqueta:

  **`QA` + `testing`**:
  - Para TODOS los reportes de ejecución de casos de prueba
  - Se usa cuando el issue sigue la estructura completa: "Casos de Prueba - [CÓDIGO]"
  - Incluye tanto tests que pasaron como los que fallaron
  - Es documentación de lo que se probó, independientemente del resultado
  - Ejemplo: "Casos de Prueba - HU-C01: Acceso mediante QR" (aunque encuentre bugs)

  **`QA` + `bug`**:
  - Solo para reportes simples y específicos de bugs
  - No sigue la estructura completa de casos de prueba
  - Formato más directo: descripción, reproducción, solución propuesta
  - Enfocado en el bug específico, no en la ejecución de tests
  - Ejemplo: "[BUG] Error 500 en login sin estructura de test cases"

  **Regla general**: Si tu issue tiene la sección "Test Cases Ejecutados", usa `testing`. Si solo reportas un bug sin esa estructura, usa `bug`.

  ---
  3. ESTRUCTURA DEL CONTENIDO

  # Casos de Prueba - [CÓDIGO]: [Nombre]

  ## Información General

  - **Historia de Usuario / Caso de Uso**: [CÓDIGO]
  - **Descripción**: [Descripción breve de qué se está probando]
  - **Fecha de Ejecución**: [DD de Mes YYYY]
  - **Tester**: [Nombre completo]
  - **Metodología**: [Automatizada / Manual / Híbrida]
  - **Ambiente**: Backend [producción/local] ([URL])

  ---

  ## Test Cases Ejecutados

  ### TC-001: [Nombre del test case]
  - **Objetivo**: [Qué valida este test]
  - **Método**: [Script bash / Manual / etc.]
  - **Pasos**:
    1. [Paso 1]
    2. [Paso 2]
    3. [Paso 3]
  - **Resultado Esperado**: [Lo que debería pasar]
  - **Resultado Obtenido**: [Lo que realmente pasó]
  - **Status**: [pass / fail / skip]

  ### TC-002: [Nombre del test case]
  ...

  [Repetir para cada test case]

  ---

  ## Resultados

  ### Resumen Ejecutivo
  Total:     X tests
  Pasados:   X (XX%)
  Fallidos:  X (XX%)
  Bloqueados: X

  ### Captura de Pantalla

  ![Ejecución del script](URL_A_LA_IMAGEN)

  _Captura de la terminal ejecutando el script de pruebas_

  ---

  ## Script de Pruebas

  **Ubicación:** `tests/qa/[nombre_script].sh`

  **Ejecución:**
  ```bash
  cd tests/qa
  ./[nombre_script].sh

  ---
  Endpoints Probados

  GET    /api/v1/[endpoint]      # Descripción
  POST   /api/v1/[endpoint]      # Descripción
  PATCH  /api/v1/[endpoint]      # Descripción
  DELETE /api/v1/[endpoint]      # Descripción

  ---
  Análisis de Fallos

  Problemas Identificados

  [Problema 1]:
  - Causa: [Descripción de la causa]
  - Recomendación: [Qué se debe hacer]

  [Problema 2]:
  ...

  ---
  Issues Relacionados

  - Issue #XX - [Descripción]
  - [Código HU/CU] - Historia de Usuario / Caso de Uso base

  ---
  Estado Final

  [Elegir uno:]

  Aprobado - Todos los tests pasaron correctamente

  Aprobado con observaciones - Funcionalidad core aprobada, [X] issues menores identificados

  No aprobado - [X] tests críticos fallaron. Requiere corrección antes de aprobar.

  Bloqueado - No se pudo ejecutar. Depende de [lo que bloquea].

  ---
  Tester: [Nombre Completo]Equipo: QA/SEGFecha: [DD de Mes YYYY]

  ---

  ## **4. CÓMO SUBIR LA CAPTURA DE PANTALLA**

  ### Opción Recomendada: Subir al repositorio (Recomendado para automatización)
  1. Guardar screenshot en `tests/qa/screenshots/`
     ```bash
     # Ejemplo: ss_test_hu_c01_acceso_mesa.png
     cp screenshot.png tests/qa/screenshots/ss_test_hu_c01_acceso_mesa.png
     ```
  2. Hacer commit y push
     ```bash
     git add tests/qa/screenshots/
     git commit -m "Agregar capturas de pruebas QA"
     git push origin BRANCH
     ```
  3. Referenciar en el issue usando GitHub raw URL:
     ```markdown
     ![Ejecución del script](https://raw.githubusercontent.com/OWNER/REPO/BRANCH/tests/qa/screenshots/FILENAME.png)
     ```
  4. **Ejemplo real**:
     ```markdown
     ![Ejecución del script](https://raw.githubusercontent.com/dp2-eder/back-dp2/qa/tests/qa/screenshots/ss_test_hu_c01_acceso_mesa.png)
     ```

  **Ventajas**:
  - Control de versiones de capturas
  - URLs predecibles y consistentes
  - No depende de servicios externos
  - Facilita automatización con scripts

  ### Opción Alternativa: Directamente en GitHub
  1. Al crear/editar el issue, arrastra la imagen a la caja de texto
  2. GitHub la subirá automáticamente a `user-attachments/assets/`
  3. Usa esa URL en el markdown: `![Descripción](URL)`

  **Nota**: Esta opción requiere acción manual, pero es útil para pruebas rápidas



  ## **5. EJEMPLO COMPLETO**

  ```markdown
  # Casos de Prueba - HU-C09: Validar carrito de compras

  ## Información General

  - **Historia de Usuario**: HU-C09
  - **Descripción**: Cliente puede revisar su carrito antes de confirmar
  - **Fecha de Ejecución**: 31 de Octubre 2025
  - **Tester**: Kevin Antonio Navarro Carrera
  - **Metodología**: Automatizada (Bash + curl)
  - **Ambiente**: Backend producción (https://back-dp2.onrender.com)

  ---

  ## Test Cases Ejecutados

  ### TC-001: Crear carrito vacío
  - **Objetivo**: Validar que se puede crear un carrito sin items
  - **Método**: Script bash automatizado
  - **Pasos**:
    1. Ejecutar POST /api/v1/carrito con sesión válida
    2. Validar respuesta HTTP 201
    3. Verificar que items = []
  - **Resultado Esperado**: Carrito creado vacío
  - **Resultado Obtenido**: Carrito creado correctamente
  - **Status**: pass

  ### TC-002: Agregar item al carrito
  - **Objetivo**: Validar que se puede agregar un producto
  - **Método**: Script bash automatizado
  - **Pasos**:
    1. POST /api/v1/carrito/add-item con producto válido
    2. Validar HTTP 200
    3. Verificar que items.length = 1
  - **Resultado Esperado**: Item agregado al carrito
  - **Resultado Obtenido**: Item agregado correctamente
  - **Status**: pass

  ---

  ## Resultados

  ### Resumen Ejecutivo
  Total:     10 tests
  Pasados:   9 (90%)
  Fallidos:  1 (10%)
  Bloqueados: 0

  ### Captura de Pantalla

  ![Ejecución del script](https://.../ABC123.png)

  _Terminal mostrando la ejecución exitosa de 9/10 tests_

  ---

  ## Script de Pruebas

  **Ubicación:** `tests/qa/test_hu_c09_carrito.sh`

  **Ejecución:**
  ```bash
  cd tests/qa
  ./test_hu_c09_carrito.sh

  ---
  Endpoints Probados

  POST   /api/v1/carrito/           # Crear carrito
  POST   /api/v1/carrito/add-item   # Agregar item
  GET    /api/v1/carrito/{id}       # Consultar carrito
  DELETE /api/v1/carrito/{id}       # Eliminar carrito

  ---
  Análisis de Fallos

  Problemas Identificados

  TC-005 - Eliminar item inexistente:
  - Causa: Backend retorna 500 en lugar de 404
  - Recomendación: Corregir manejo de errores para retornar 404

  ---
  Issues Relacionados

  - HU-C09 - Historia de Usuario base

  ---
  Estado Final

  Aprobado con observaciones - Funcionalidad core aprobada, 1 issue menor de manejo de errores identificado.

  ---
  Tester: Kevin Antonio Navarro CarreraEquipo: QA/SEGFecha: 31 de Octubre 2025

  ---

  ## **6. GUÍA DE ESTILO Y BUENAS PRÁCTICAS**

  ### Formalismo y Legibilidad

  Para mantener un estándar profesional en la documentación de QA:

  1. **Evitar emojis en el contenido**: Aunque pueden ser visuales, los emojis restan formalismo al reporte. Usar texto descriptivo en su lugar.
     - Incorrecto: `✅ APROBADO - Todos los tests pasaron`
     - Correcto: `Aprobado - Todos los tests pasaron correctamente`

  2. **No usar palabras completamente en MAYÚSCULAS**: El uso constante de mayúsculas dificulta la lectura y reduce el formalismo.
     - Incorrecto: `Status: PASS`, `FAIL`, `SKIP`
     - Correcto: `Status: pass`, `fail`, `skip`

  3. **Capitalización de títulos**: Usar capitalización normal en títulos y secciones.
     - Correcto: `Casos de Prueba - HU-C01: Acceso mediante QR`
     - Correcto: `Información General`, `Test Cases Ejecutados`

  4. **Capturas de pantalla obligatorias**: Siempre adjuntar capturas de la ejecución del script en terminal.
     - Muestra evidencia visual del resultado
     - Facilita la revisión y auditoría
     - Proporciona contexto adicional sobre el ambiente de ejecución

  5. **Usar negritas solo para etiquetas de campo**:
     - Correcto: `- **Objetivo**: Validar que el endpoint retorna lista`
     - Incorrecto: Usar negritas en el contenido del texto

  ### Ejemplo de Status Correcto
  ```markdown
  - Status: pass
  - Status: fail
  - Status: skip
  ```

  ### Ejemplo de Estado Final Correcto
  ```markdown
  ## Estado Final

  Aprobado - Todos los tests pasaron correctamente

  Aprobado con observaciones - Funcionalidad core aprobada, 1 issue menor identificado.

  No aprobado - 3 tests críticos fallaron. Requiere corrección antes de aprobar.

  Bloqueado - No se pudo ejecutar. Depende de corrección en endpoint de autenticación.
  ```

  ---

  ## **7. Perspectiva QA - Reportes basados en testing**

  ### Mantener el rol de QA

  Los reportes de bugs y casos de prueba deben reflejar la perspectiva de QA (testing/black-box), no de desarrollo interno. Esto ayuda a:
  - Mantener objetividad en los reportes
  - Evitar que parezcan generados automáticamente
  - Respetar la separación de roles entre QA y Desarrollo
  - Basar los reportes en observaciones reales de pruebas

  ### Qué incluir en reportes de QA

  **Basado en pruebas y observaciones:**
  - Endpoints probados y respuestas obtenidas
  - Comportamiento esperado vs comportamiento observado
  - Pasos de reproducción desde la perspectiva del usuario/API
  - Datos de prueba utilizados
  - Resultados de ejecución de scripts de testing

  **Ejemplo correcto:**
  ```markdown
  Al intentar crear una relación usando POST /api/v1/productos-alergenos,
  recibo error 404. Probé con diferentes IDs válidos y el resultado es
  el mismo. Otros endpoints relacionados (GET /productos, GET /alergenos)
  funcionan correctamente.
  ```

  ### Qué evitar en reportes de QA

  **Detalles internos de implementación:**
  - Rutas de archivos de código fuente (`src/api/controllers/...`)
  - Nombres de clases, métodos o servicios internos
  - Detalles de la arquitectura interna del backend
  - Análisis del código fuente (eso es trabajo de desarrollo)

  **Ejemplo incorrecto:**
  ```markdown
  El controller existe en src/api/controllers/producto_alergeno_controller.py
  pero no está registrado en src/main.py líneas 185-217. El servicio
  ProductoAlergenoService no tiene validación en el método create_producto_alergeno().
  ```

  ### Severidad e impacto

  **QA NO ASIGNA SEVERIDAD NI IMPACTO**
  - QA reporta HECHOS observados, no evaluaciones de severidad
  - Asignar prioridad/impacto es responsabilidad de Product/Development
  - En lugar de calificar, describir objetivamente qué funcionalidades NO funcionan
  - Usar sección "Funcionalidades Afectadas" en lugar de "Impacto"

  **Enfoque correcto (objetivo):**
  ```markdown
  ## Funcionalidades Afectadas
  - No es posible asignar alérgenos a productos mediante la API
  - Bloquea flujo de gestión de alérgenos en HU-A04
  - Cliente no puede completar el registro sin conocer ID de rol
  ```

  **Enfoques INCORRECTOS (subjetivos - NO usar):**
  ```markdown
  ## Impacto
  - Severidad: Alta
  - Impacto: Crítico
  - Prioridad: MEDIO-ALTO
  ```

  ```markdown
  ## Impacto
  - Cliente no puede volver a entrar si olvidó cerrar sesión
  - Error 500 genera mala experiencia de usuario
  - Contamina logs con errores internos
  ```

  **¿Por qué está mal?** Frases como "mala experiencia", "contamina logs", "bloquear indefinidamente" son INTERPRETACIONES, no hechos observados.

  ### Soluciones propuestas

  **QA NO PROPONE SOLUCIONES - Solo reporta observaciones:**
  - QA no debe sugerir cómo implementar correcciones
  - QA no debe recomendar cambios técnicos o de diseño
  - Implementar soluciones es responsabilidad exclusiva de Desarrollo
  - El rol de QA es reportar comportamiento observado vs esperado

  **Sí definir criterios de aceptación para validar el fix:**
  - Especificar qué debe validarse cuando se corrija
  - Definir los casos de prueba para verificar el fix
  - Describir el comportamiento esperado desde perspectiva del usuario/API

  **Ejemplo correcto:**
  ```markdown
  ## Para validar cuando se corrija
  1. POST /api/v1/productos-alergenos debería crear la relación y retornar 201
  2. Verificar que GET /productos/{id}/alergenos muestre el alérgeno asignado
  3. Verificar que DELETE funcione para eliminar la relación
  ```

  **Ejemplos incorrectos:**
  ```markdown
  ## Recomendación
  Hacer id_rol opcional y asignar automáticamente el rol "cliente"
  ```

  ```markdown
  ## Solución Propuesta
  Registrar el router en src/main.py:
  ```python
  app.include_router(producto_alergeno_controller.router, prefix="/api/v1")
  ```
  ```

  ### Lenguaje natural

  - Evitar estructuras demasiado rígidas o repetitivas que parezcan generadas automáticamente
  - Usar lenguaje directo y profesional, pero natural
  - Variar la forma de expresar ideas similares
  - Escribir como lo harías en un email profesional al equipo

  ---

  ## **8. CHECKLIST ANTES DE PUBLICAR**

  - [ ] Título sigue el formato: `Casos de Prueba - [CÓDIGO]: [Nombre]`
  - [ ] Etiquetas: `QA` + `testing`/`bug`
  - [ ] Fecha de ejecución incluida
  - [ ] Nombre del tester incluido
  - [ ] Todos los TC tienen resultado (pass/fail/skip) sin mayúsculas
  - [ ] Resumen de resultados incluido
  - [ ] Captura de pantalla de terminal incluida (obligatorio)
  - [ ] Script ubicación especificada
  - [ ] Estado final sin emojis
  - [ ] No se usan palabras completamente en MAYÚSCULAS
  - [ ] No se usan emojis en el contenido del issue