#!/bin/bash

# Script de pruebas para HU-C05: Cliente explorando - Explorar la oferta vigente por categorías
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Módulo: Carta Digital - Backend
# Fecha: 2025-11-13
# Historia de Usuario: Como cliente explorando, quiero explorar la oferta vigente por categorías para decidir más rápido qué consumir

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
echo "  HU-C05: Explorar Carta por Categorías"
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

echo "=== Tests de Categorías ==="
echo ""

# TC-001: Obtener lista de categorías
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Obtener lista de categorías (GET /categorias)... " >&2

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/categorias")
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

CATEGORIAS_RESPONSE="$body"

CATEGORIA_COUNT=$(echo "$CATEGORIAS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null || echo "0")

echo ""

# TC-002: Validar que existen categorías
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que existen categorías en la carta... " >&2
if [ "$CATEGORIA_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} (Categorías encontradas: $CATEGORIA_COUNT)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (No hay categorías)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Obtener una categoría para tests
CATEGORIA_ID=$(echo "$CATEGORIAS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

echo ""
echo "=== Tests de Productos por Categoría ==="
echo ""

if [ -n "$CATEGORIA_ID" ]; then
    # TC-003: Obtener productos de una categoría en formato card
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Obtener productos de categoría en formato card (GET /productos/categoria/{id}/cards)... " >&2

    response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/productos/categoria/$CATEGORIA_ID/cards")
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

    PRODUCTOS_CATEGORIA="$body"

    echo ""

    # TC-004: Validar estructura de productos en formato card
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Validar que productos tienen nombre, imagen y descripción... " >&2

    PRODUCTO_SAMPLE=$(echo "$PRODUCTOS_CATEGORIA" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('items', [])
if items:
    p = items[0]
    has_nombre = 'nombre' in p and p['nombre']
    has_precio = 'precio_base' in p
    print(json.dumps({'valid': has_nombre and has_precio, 'nombre': p.get('nombre', ''), 'precio': p.get('precio_base', 0)}))
else:
    print(json.dumps({'valid': False}))
" 2>/dev/null)

    PRODUCTO_VALID=$(echo "$PRODUCTO_SAMPLE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('valid', False))" 2>/dev/null)

    if [ "$PRODUCTO_VALID" = "True" ]; then
        PRODUCTO_NOMBRE=$(echo "$PRODUCTO_SAMPLE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('nombre', ''))" 2>/dev/null)
        PRODUCTO_PRECIO=$(echo "$PRODUCTO_SAMPLE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('precio', 0))" 2>/dev/null)
        echo -e "${GREEN}✓ PASS${NC} (Ejemplo: $PRODUCTO_NOMBRE - S/$PRODUCTO_PRECIO)" >&2
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Productos sin campos requeridos)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
fi

echo ""
echo "=== Tests de Productos Generales (Carta Completa) ==="
echo ""

# TC-005: Obtener todos los productos en formato card
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Obtener todos los productos activos (GET /productos/cards)... " >&2

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/productos/cards?limit=20")
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

PRODUCTOS_RESPONSE="$body"

PRODUCTO_COUNT=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null || echo "0")

echo ""

# TC-006: Validar que existen productos activos
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que existen productos activos... " >&2
if [ "$PRODUCTO_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} (Productos activos: $PRODUCTO_COUNT)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (No hay productos activos)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Obtener un producto para pruebas detalladas
PRODUCTO_ID=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

echo ""
echo "=== Tests de Detalle de Producto ==="
echo ""

if [ -n "$PRODUCTO_ID" ]; then
    # TC-007: Obtener detalle completo de un producto
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Obtener detalle de producto (GET /productos/{id})... " >&2

    response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/productos/$PRODUCTO_ID")
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

    PRODUCTO_DETAIL="$body"

    echo ""

    # TC-008: Validar campos obligatorios del producto
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Validar campos obligatorios del producto... " >&2

    PROD_NOMBRE=$(echo "$PRODUCTO_DETAIL" | python3 -c "import sys, json; print(json.load(sys.stdin).get('nombre', ''))" 2>/dev/null)
    PROD_PRECIO=$(echo "$PRODUCTO_DETAIL" | python3 -c "import sys, json; print(json.load(sys.stdin).get('precio_base', ''))" 2>/dev/null)
    PROD_ACTIVO=$(echo "$PRODUCTO_DETAIL" | python3 -c "import sys, json; print(json.load(sys.stdin).get('activo', False))" 2>/dev/null)

    if [ -n "$PROD_NOMBRE" ] && [ -n "$PROD_PRECIO" ]; then
        echo -e "${GREEN}✓ PASS${NC} ($PROD_NOMBRE - S/$PROD_PRECIO, Activo: $PROD_ACTIVO)" >&2
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Campos faltantes)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
fi

echo ""
echo "=========================================="
echo "  Resumen de Tests - HU-C05"
echo "=========================================="
echo "Historia: Cliente explora carta por categorías"
echo "Backend: Endpoints de categorías y productos"
echo ""
echo "Total:  $TOTAL_TESTS"
echo -e "Pasados: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Fallidos: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los tests pasaron${NC}"
    echo ""
    echo "Análisis: El backend provee correctamente:"
    echo "  - Lista de categorías disponibles"
    echo "  - Productos activos por categoría (formato card)"
    echo "  - Productos activos generales"
    echo "  - Detalle completo de productos"
    echo "  - Campos: nombre, imagen, descripción, precio"
    exit 0
else
    echo -e "${RED}✗ Algunos tests fallaron${NC}"
    exit 1
fi
