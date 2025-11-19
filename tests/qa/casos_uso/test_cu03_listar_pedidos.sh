#!/bin/bash

# Script de pruebas para Caso de Uso 3: Listar pedidos
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Modulo: Pedidos - Backend
# Fecha: 2025-10-29

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_URL="${API_URL:-https://back-dp2.onrender.com}"
VERBOSE="${VERBOSE:-false}"

echo "=========================================="
echo "  CU-03: Listar Pedidos"
echo "=========================================="
echo ""
echo "API Base URL: $API_URL"
COMMIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "N/A")
echo "Commit: $COMMIT_HASH"
echo "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_name="$1"
    local expected_status="$2"
    shift 2

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: $test_name... " >&2

    response=$("$@")
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "$body"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: $expected_status, Got: $status_code)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "$body"
        return 1
    fi
}

echo "=== Tests de Listado de Pedidos ==="
echo ""

# TC-001: Listar pedidos sin filtros
PEDIDOS_RESPONSE=$(run_test "Listar pedidos (GET /pedidos)" "200" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos")

echo ""

# TC-002: Validar estructura de respuesta paginada
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar estructura de respuesta paginada... "
HAS_ITEMS=$(echo "$PEDIDOS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print('items' in data)" 2>/dev/null)
HAS_TOTAL=$(echo "$PEDIDOS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print('total' in data)" 2>/dev/null)

if [ "$HAS_ITEMS" = "True" ] && [ "$HAS_TOTAL" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Campos: items, total presentes)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Estructura incorrecta)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-003: Listar pedidos con paginación (skip y limit)
run_test "Listar pedidos con paginación (skip=0, limit=5)" "200" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos?skip=0&limit=5"

echo ""

# TC-004: Validar que limit funciona correctamente
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que limit=5 retorna máximo 5 items... "
PEDIDOS_LIMIT=$(curl -s "$API_URL/api/v1/pedidos?skip=0&limit=5")
ITEMS_COUNT=$(echo "$PEDIDOS_LIMIT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null)

if [ "$ITEMS_COUNT" -le 5 ]; then
    echo -e "${GREEN}✓ PASS${NC} (Items retornados: $ITEMS_COUNT <= 5)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Items retornados: $ITEMS_COUNT > 5)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=== Tests de Filtros de Pedidos ==="
echo ""

# TC-005: Filtrar pedidos por estado pendiente
run_test "Filtrar por estado pendiente" "200" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos?estado=pendiente"

# TC-006: Filtrar pedidos por estado confirmado
run_test "Filtrar por estado confirmado" "200" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos?estado=confirmado"

# TC-007: Filtrar pedidos por estado en_preparacion
run_test "Filtrar por estado en_preparacion" "200" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos?estado=en_preparacion"

echo ""

# TC-008: Obtener ID de mesa para filtro
echo -n "Obteniendo ID de mesa para filtro... "
MESA_ID=$(curl -s "$API_URL/api/v1/mesas?limit=1" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

if [ -n "$MESA_ID" ]; then
    echo -e "${GREEN}✓${NC} Mesa ID: $MESA_ID"

    # TC-009: Filtrar pedidos por mesa
    run_test "Filtrar por ID de mesa" "200" \
        curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos?id_mesa=$MESA_ID"
else
    echo -e "${YELLOW}⚠ SKIP${NC} - No hay mesas disponibles"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

echo ""
echo "=== Tests de Validación de Datos ==="
echo ""

# TC-010: Validar campos requeridos en items del listado
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar campos requeridos en pedidos... "
FIRST_PEDIDO=$(curl -s "$API_URL/api/v1/pedidos?limit=1")
HAS_ID=$(echo "$FIRST_PEDIDO" | python3 -c "import sys, json; data = json.load(sys.stdin); print('id' in data['items'][0] if data.get('items') else False)" 2>/dev/null)
HAS_NUMERO=$(echo "$FIRST_PEDIDO" | python3 -c "import sys, json; data = json.load(sys.stdin); print('numero_pedido' in data['items'][0] if data.get('items') else False)" 2>/dev/null)
HAS_ESTADO=$(echo "$FIRST_PEDIDO" | python3 -c "import sys, json; data = json.load(sys.stdin); print('estado' in data['items'][0] if data.get('items') else False)" 2>/dev/null)
HAS_TOTAL=$(echo "$FIRST_PEDIDO" | python3 -c "import sys, json; data = json.load(sys.stdin); print('total' in data['items'][0] if data.get('items') else False)" 2>/dev/null)

if [ "$HAS_ID" = "True" ] && [ "$HAS_NUMERO" = "True" ] && [ "$HAS_ESTADO" = "True" ] && [ "$HAS_TOTAL" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Campos: id, numero_pedido, estado, total)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Faltan campos requeridos)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=========================================="
echo "  Resumen de Tests"
echo "=========================================="
echo "Total:  $TOTAL_TESTS"
echo -e "Pasados: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Fallidos: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los tests pasaron${NC}"
    exit 0
else
    echo -e "${RED}✗ Algunos tests fallaron${NC}"
    exit 1
fi
