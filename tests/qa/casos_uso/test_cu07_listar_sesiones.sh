#!/bin/bash

# Script de pruebas para Caso de Uso 7: Listar sesiones
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Modulo: Sesiones - Backend
# Fecha: 2025-10-29

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_URL="${API_URL:-https://back-dp2.onrender.com}"
VERBOSE="${VERBOSE:-false}"

echo "=========================================="
echo "  CU-07: Listar Sesiones"
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

echo "=== Tests de Listado de Sesiones ==="
echo ""

# TC-001: Listar sesiones sin filtros
SESIONES_RESPONSE=$(run_test "Listar sesiones (GET /sesiones)" "200" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/sesiones/")

echo ""

# TC-002: Validar estructura de respuesta paginada
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar estructura de respuesta paginada... "
HAS_ITEMS=$(echo "$SESIONES_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print('items' in data)" 2>/dev/null)
HAS_TOTAL=$(echo "$SESIONES_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print('total' in data)" 2>/dev/null)

if [ "$HAS_ITEMS" = "True" ] && [ "$HAS_TOTAL" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Campos: items, total presentes)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Estructura incorrecta)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-003: Listar sesiones con paginación (skip y limit)
run_test "Listar sesiones con paginación (skip=0, limit=5)" "200" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/sesiones/?skip=0&limit=5"

echo ""

# TC-004: Validar que limit funciona correctamente
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que limit=5 retorna máximo 5 items... "
SESIONES_LIMIT=$(curl -s "$API_URL/api/v1/sesiones/?skip=0&limit=5")
ITEMS_COUNT=$(echo "$SESIONES_LIMIT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null)

if [ "$ITEMS_COUNT" -le 5 ]; then
    echo -e "${GREEN}✓ PASS${NC} (Items retornados: $ITEMS_COUNT <= 5)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Items retornados: $ITEMS_COUNT > 5)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=== Tests de Filtros por Estado ==="
echo ""

# TC-005: Filtrar sesiones por estado activo
run_test "Filtrar por estado activo" "200" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/sesiones/estado/activo"

# TC-006: Filtrar sesiones por estado inactivo
run_test "Filtrar por estado inactivo" "200" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/sesiones/estado/inactivo"

# TC-007: Filtrar sesiones por estado cerrado
run_test "Filtrar por estado cerrado" "200" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/sesiones/estado/cerrado"

echo ""
echo "=== Tests de Filtros por Local ==="
echo ""

# TC-008: Obtener ID de local para filtro
echo -n "Obteniendo ID de local para filtro... "
LOCAL_ID=$(curl -s "$API_URL/api/v1/locales?limit=1" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

if [ -n "$LOCAL_ID" ]; then
    echo -e "${GREEN}✓${NC} Local ID: $LOCAL_ID"

    # TC-009: Filtrar sesiones por local
    run_test "Filtrar por ID de local" "200" \
        curl -s -w "\n%{http_code}" "$API_URL/api/v1/sesiones/local/$LOCAL_ID"
else
    echo -e "${YELLOW}⚠ SKIP${NC} - No hay locales disponibles"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

echo ""
echo "=== Tests de Validación de Datos ==="
echo ""

# TC-010: Validar campos requeridos en items del listado
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar campos requeridos en sesiones... "
FIRST_SESION=$(curl -s "$API_URL/api/v1/sesiones/?limit=1")
HAS_ID=$(echo "$FIRST_SESION" | python3 -c "import sys, json; data = json.load(sys.stdin); print('id' in data['items'][0] if data.get('items') and len(data['items']) > 0 else False)" 2>/dev/null)
HAS_ID_LOCAL=$(echo "$FIRST_SESION" | python3 -c "import sys, json; data = json.load(sys.stdin); print('id_local' in data['items'][0] if data.get('items') and len(data['items']) > 0 else False)" 2>/dev/null)
HAS_ESTADO=$(echo "$FIRST_SESION" | python3 -c "import sys, json; data = json.load(sys.stdin); print('estado' in data['items'][0] if data.get('items') and len(data['items']) > 0 else False)" 2>/dev/null)
HAS_FECHA_INICIO=$(echo "$FIRST_SESION" | python3 -c "import sys, json; data = json.load(sys.stdin); print('fecha_inicio' in data['items'][0] if data.get('items') and len(data['items']) > 0 else False)" 2>/dev/null)

if [ "$HAS_ID" = "True" ] && [ "$HAS_ID_LOCAL" = "True" ] && [ "$HAS_ESTADO" = "True" ] && [ "$HAS_FECHA_INICIO" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Campos: id, id_local, estado, fecha_inicio)"
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
