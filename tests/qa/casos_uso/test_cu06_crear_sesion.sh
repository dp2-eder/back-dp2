#!/bin/bash

# Script de pruebas para Caso de Uso 6: Crear sesión
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
echo "  CU-06: Crear Sesión"
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
        if [ "$VERBOSE" = "true" ]; then
            echo "Response: $body"
        fi
        echo "$body"
        return 1
    fi
}

echo "=== Preparación: Obtener ID de local ==="
echo ""

# Obtener ID de un local
echo -n "Obteniendo ID de local... "
LOCAL_RESPONSE=$(curl -s "$API_URL/api/v1/locales?limit=1")
LOCAL_ID=$(echo "$LOCAL_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

if [ -n "$LOCAL_ID" ]; then
    echo -e "${GREEN}✓${NC} Local ID: $LOCAL_ID"
else
    echo -e "${RED}✗ No se encontraron locales${NC}"
    exit 1
fi

echo ""
echo "=== Tests de Creación de Sesión ==="
echo ""

# TC-001: Crear sesión nueva
PAYLOAD=$(cat <<EOF
{
  "id_local": "$LOCAL_ID",
  "estado": "activo", "id_domotica": "TEST-DOM-001"
}
EOF
)

SESION_RESPONSE=$(run_test "Crear sesión nueva" "201" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/sesiones/" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

SESION_ID=$(echo "$SESION_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

echo ""

# TC-002: Validar que la sesión tiene ID generado (ULID)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que sesión tiene ID generado (ULID)... "
if [ -n "$SESION_ID" ] && [ ${#SESION_ID} -eq 26 ]; then
    echo -e "${GREEN}✓ PASS${NC} (ID: $SESION_ID)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (ID inválido o vacío)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-003: Validar estado inicial es ACTIVO
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que estado es activo... "
ESTADO=$(echo "$SESION_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('estado', ''))" 2>/dev/null)

if [ "$ESTADO" = "activo" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Estado: $ESTADO)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: activo, Obtenido: $ESTADO)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-004: Validar que tiene id_local correcto
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que id_local es correcto... "
ID_LOCAL_RESP=$(echo "$SESION_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id_local', ''))" 2>/dev/null)

if [ "$ID_LOCAL_RESP" = "$LOCAL_ID" ]; then
    echo -e "${GREEN}✓ PASS${NC} (ID Local: $ID_LOCAL_RESP)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: $LOCAL_ID, Obtenido: $ID_LOCAL_RESP)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-005: Validar que tiene fecha_inicio
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que fecha_inicio no es null... "
FECHA_INICIO=$(echo "$SESION_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('fecha_inicio', 'null'))" 2>/dev/null)

if [ "$FECHA_INICIO" != "null" ] && [ "$FECHA_INICIO" != "None" ] && [ -n "$FECHA_INICIO" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Fecha inicio: $FECHA_INICIO)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (fecha_inicio es null)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-006: Validar que fecha_fin es null (sesión activa)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que fecha_fin es null (sesión activa)... "
FECHA_FIN=$(echo "$SESION_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(str(data.get('fecha_fin', 'null')))" 2>/dev/null)

if [ "$FECHA_FIN" = "null" ] || [ "$FECHA_FIN" = "None" ]; then
    echo -e "${GREEN}✓ PASS${NC} (fecha_fin: null)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (fecha_fin no es null: $FECHA_FIN)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=== Tests de Consulta de Sesión ==="
echo ""

if [ -n "$SESION_ID" ]; then
    # TC-007: Obtener sesión por ID
    run_test "Obtener sesión por ID (GET /sesiones/{id})" "200" \
        curl -s -w "\n%{http_code}" "$API_URL/api/v1/sesiones/$SESION_ID"
else
    echo -e "${YELLOW}⚠ SKIP${NC} - No se pudo crear sesión"
fi

echo ""
echo "=== Tests de Validación ==="
echo ""

# TC-008: Crear sesión con local inexistente debe fallar
PAYLOAD_LOCAL_INVALIDO=$(cat <<EOF
{
  "id_local": "01INVALID000000000000000000",
  "estado": "activo", "id_domotica": "TEST-DOM-001"
}
EOF
)

run_test "Crear sesión con local inexistente debe retornar 400" "400" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/sesiones/" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_LOCAL_INVALIDO"

# TC-009: Crear sesión con estado inválido
PAYLOAD_ESTADO_INVALIDO=$(cat <<EOF
{
  "id_local": "$LOCAL_ID",
  "estado": "ESTADO_INVALIDO"
}
EOF
)

run_test "Crear sesión con estado inválido debe retornar 400 o 422" "422" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/sesiones/" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_ESTADO_INVALIDO"

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
