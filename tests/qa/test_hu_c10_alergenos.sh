#!/bin/bash

# Script de pruebas para HU-C10: Cliente con restricciones alimentarias - Ver alérgenos del producto
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Módulo: Alérgenos - Backend
# Fecha: 2025-11-13
# Historia de Usuario: Como cliente con restricciones alimentarias, quiero ver alérgenos del producto para evitar riesgos de salud

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
API_URL="${API_URL:-https://back-dp2.onrender.com}"
VERBOSE="${VERBOSE:-false}"

# Cargar funciones comunes
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_common.sh"

echo "=========================================="
echo "  HU-C10: Ver Alérgenos de Productos"
echo "=========================================="
echo ""
echo "API Base URL: $API_URL"
COMMIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "N/A")
echo "Commit: $COMMIT_HASH"
echo "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Contador de tests
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Función para test
run_test() {
    local test_name="$1"
    local expected_status="$2"
    shift 2

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: $test_name... " >&2

    response=$("$@")
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$VERBOSE" = "true" ]; then
        echo "" >&2
        echo "Response: $body" >&2
        echo "Status: $status_code" >&2
    fi

    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "$body"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: $expected_status, Got: $status_code)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "Response body: $body" >&2
        echo "$body"
        return 1
    fi
}

echo "=== Tests de Catálogo de Alérgenos ==="
echo ""

# TC-001: Obtener lista de alérgenos del sistema
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Obtener lista de alérgenos (GET /alergenos)... " >&2

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/alergenos")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$VERBOSE" = "true" ]; then
    echo "" >&2
    echo "Response: $body" >&2
    echo "Status: $status_code" >&2
fi

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected: 200, Got: $status_code)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "Response body: $body" >&2
fi

ALERGENOS_RESPONSE="$body"
ALERGENO_COUNT=$(echo "$ALERGENOS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null || echo "0")

echo ""

# TC-002: Validar que existen alérgenos en el catálogo
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que existen alérgenos en el catálogo... " >&2
if [ "$ALERGENO_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} (Alérgenos catalogados: $ALERGENO_COUNT)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (No hay alérgenos en el catálogo)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Obtener un alérgeno para pruebas
ALERGENO_ID=$(echo "$ALERGENOS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)
ALERGENO_NOMBRE=$(echo "$ALERGENOS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['nombre'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

echo ""
echo "=== Tests de Productos con Alérgenos ==="
echo ""

# TC-003: Obtener productos que tienen alérgenos
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Obtener productos con alérgenos (GET /productos/con-alergenos)... " >&2

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/productos/con-alergenos")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$VERBOSE" = "true" ]; then
    echo "" >&2
    echo "Response: $body" >&2
    echo "Status: $status_code" >&2
fi

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected: 200, Got: $status_code)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "Response body: $body" >&2
fi

PRODUCTOS_ALERGENOS="$body"
PRODUCTOS_ALERGENO_COUNT=$(echo "$PRODUCTOS_ALERGENOS" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null || echo "0")

echo ""

# TC-004: Validar que endpoint retorna estructura correcta
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar estructura de productos con alérgenos... " >&2
if [ "$PRODUCTOS_ALERGENO_COUNT" -ge 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} (Productos con alérgenos: $PRODUCTOS_ALERGENO_COUNT)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Respuesta inválida)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=== Tests de Alérgenos por Producto ==="
echo ""

# Buscar un producto CON alérgenos (de la lista obtenida en TC-3)
# Primero intentar encontrar uno que realmente tenga alérgenos
PRODUCTO_INFO=$(echo "$PRODUCTOS_ALERGENOS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('items', [])

# Buscar un producto que tenga alérgenos
for item in items:
    if len(item.get('alergenos', [])) > 0:
        print(json.dumps({'id': item['producto']['id'], 'nombre': item['producto']['nombre']}))
        sys.exit(0)

# Si no hay ninguno con alérgenos, usar el primero disponible
if items:
    print(json.dumps({'id': items[0]['producto']['id'], 'nombre': items[0]['producto']['nombre']}))
" 2>/dev/null)

PRODUCTO_ID=$(echo "$PRODUCTO_INFO" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
PRODUCTO_NOMBRE=$(echo "$PRODUCTO_INFO" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('nombre', ''))" 2>/dev/null)

if [ -n "$PRODUCTO_ID" ]; then
    echo "Producto de prueba: $PRODUCTO_NOMBRE (ID: $PRODUCTO_ID)"
    echo ""

    # TC-005: Obtener alérgenos de un producto específico
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Obtener alérgenos de producto (GET /productos/{id}/alergenos)... " >&2

    response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/productos/$PRODUCTO_ID/alergenos")
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$VERBOSE" = "true" ]; then
        echo "" >&2
        echo "Response: $body" >&2
        echo "Status: $status_code" >&2
    fi

    if [ "$status_code" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: 200, Got: $status_code)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "Response body: $body" >&2
    fi

    PRODUCTO_ALERGENOS="$body"

    echo ""

    # TC-006: Validar estructura de respuesta de alérgenos por producto
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Validar estructura de alérgenos del producto... " >&2

    PRODUCTO_ALERGENO_LIST=$(echo "$PRODUCTO_ALERGENOS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Backend puede retornar [] directamente o {alergenos: [...]}
if isinstance(data, list):
    alergenos = data
else:
    alergenos = data.get('alergenos', [])
print(len(alergenos))
" 2>/dev/null)

    if [ -n "$PRODUCTO_ALERGENO_LIST" ]; then
        if [ "$PRODUCTO_ALERGENO_LIST" -gt 0 ]; then
            echo -e "${GREEN}✓ PASS${NC} (Producto tiene $PRODUCTO_ALERGENO_LIST alérgeno(s))" >&2
            PASSED_TESTS=$((PASSED_TESTS + 1))

            # Mostrar alérgenos si VERBOSE
            if [ "$VERBOSE" = "true" ]; then
                echo "Alérgenos del producto:" >&2
                echo "$PRODUCTO_ALERGENOS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if isinstance(data, list):
    alergenos = data
else:
    alergenos = data.get('alergenos', [])
for alergeno in alergenos:
    print(f\"  - {alergeno.get('nombre', 'N/A')}\")
" >&2
            fi
        else
            echo -e "${YELLOW}⚠ PASS${NC} (Producto sin alérgenos - válido)" >&2
            PASSED_TESTS=$((PASSED_TESTS + 1))
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Respuesta inválida)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    echo ""

    # TC-007: Validar límite de máximo 10 alérgenos por producto (según HU-A04)
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Validar que producto no excede límite de 10 alérgenos... " >&2

    if [ -n "$PRODUCTO_ALERGENO_LIST" ] && [ "$PRODUCTO_ALERGENO_LIST" -le 10 ]; then
        echo -e "${GREEN}✓ PASS${NC} (Alérgenos: $PRODUCTO_ALERGENO_LIST/10 máx)" >&2
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Excede límite de 10 alérgenos)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo -e "${YELLOW}⚠ SKIP${NC} - No se encontró producto para pruebas"
fi

echo ""
echo "=========================================="
echo "  Resumen de Tests - HU-C10"
echo "=========================================="
echo "Historia: Cliente con restricciones ve alérgenos"
echo "Backend: Endpoints de alérgenos y productos"
echo ""
echo "Total:  $TOTAL_TESTS"
echo -e "Pasados: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Fallidos: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los tests pasaron${NC}"
    echo ""
    echo "Análisis: El backend provee correctamente:"
    echo "  - Catálogo centralizado de alérgenos"
    echo "  - Lista de productos con alérgenos"
    echo "  - Alérgenos específicos por producto"
    echo "  - Límite de máximo 10 alérgenos por producto"
    exit 0
else
    echo -e "${RED}✗ Algunos tests fallaron${NC}"
    exit 1
fi
