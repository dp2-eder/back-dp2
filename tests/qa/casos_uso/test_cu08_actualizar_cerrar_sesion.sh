#!/bin/bash

# Script de pruebas para Caso de Uso 8: Actualizar y cerrar sesión
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
echo "  CU-08: Actualizar y Cerrar Sesión"
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

echo "=== Preparación: Crear sesión de prueba ==="
echo ""

# Obtener ID de local
echo -n "Obteniendo ID de local... "
LOCAL_ID=$(curl -s "$API_URL/api/v1/locales?limit=1" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)
echo -e "${GREEN}✓${NC} $LOCAL_ID"

# Crear sesión de prueba
echo -n "Creando sesión de prueba... "
PAYLOAD_CREATE=$(cat <<EOF
{
  "id_local": "$LOCAL_ID",
  "estado": "activo", "id_domotica": "TEST-DOM-002"
}
EOF
)

SESION_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/sesiones/" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_CREATE")

SESION_ID=$(echo "$SESION_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

if [ -n "$SESION_ID" ]; then
    echo -e "${GREEN}✓${NC} Sesión ID: $SESION_ID"
else
    echo -e "${RED}✗ No se pudo crear sesión${NC}"
    exit 1
fi

echo ""
echo "=== Tests de Actualización de Sesión ==="
echo ""

# TC-001: Cambiar estado a INACTIVO
PAYLOAD_INACTIVO='{"estado": "inactivo"}'
SESION_UPDATE=$(run_test "Cambiar estado a INACTIVO" "200" \
    curl -s -w "\n%{http_code}" -X PATCH "$API_URL/api/v1/sesiones/$SESION_ID" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_INACTIVO")

echo ""

# TC-002: Validar que el estado cambió a INACTIVO
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que estado es INACTIVO... "
ESTADO=$(echo "$SESION_UPDATE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('estado', ''))" 2>/dev/null)

if [ "$ESTADO" = "inactivo" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Estado: $ESTADO)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: inactivo, Obtenido: $ESTADO)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-003: Cambiar estado a ACTIVO nuevamente
PAYLOAD_ACTIVO='{"estado": "activo", "id_domotica": "TEST-DOM-002"}'
run_test "Cambiar estado a ACTIVO" "200" \
    curl -s -w "\n%{http_code}" -X PATCH "$API_URL/api/v1/sesiones/$SESION_ID" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_ACTIVO"

echo ""
echo "=== Tests de Cerrar Sesión ==="
echo ""

# TC-004: Cambiar estado a CERRADO
PAYLOAD_CERRADO='{"estado": "cerrado"}'
SESION_CERRADO=$(run_test "Cerrar sesión (estado cerrado)" "200" \
    curl -s -w "\n%{http_code}" -X PATCH "$API_URL/api/v1/sesiones/$SESION_ID" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_CERRADO")

echo ""

# TC-005: Validar que el estado es CERRADO
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que estado es CERRADO... "
ESTADO_CERRADO=$(echo "$SESION_CERRADO" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('estado', ''))" 2>/dev/null)

if [ "$ESTADO_CERRADO" = "cerrado" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Estado: $ESTADO_CERRADO)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: cerrado, Obtenido: $ESTADO_CERRADO)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-006: Validar que fecha_fin no es null
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que fecha_fin no es null... "
FECHA_FIN=$(echo "$SESION_CERRADO" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('fecha_fin', 'null'))" 2>/dev/null)

if [ "$FECHA_FIN" != "null" ] && [ "$FECHA_FIN" != "None" ] && [ -n "$FECHA_FIN" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Fecha fin: $FECHA_FIN)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (fecha_fin es null)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=== Tests de Validación de Errores ==="
echo ""

# TC-007: Actualizar sesión inexistente
run_test "PATCH sesión inexistente debe retornar 404" "404" \
    curl -s -w "\n%{http_code}" -X PATCH "$API_URL/api/v1/sesiones/01INVALID000000000000000000" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_ACTIVO"

# TC-008: GET sesión inexistente
run_test "GET sesión inexistente debe retornar 404" "404" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/sesiones/01INVALID000000000000000000"

# TC-009: DELETE sesión inexistente
run_test "DELETE sesión inexistente debe retornar 404" "404" \
    curl -s -w "\n%{http_code}" -X DELETE "$API_URL/api/v1/sesiones/01INVALID000000000000000000"

echo ""
echo "=== Test de Eliminación de Sesión ==="
echo ""

# Crear otra sesión para eliminar
echo -n "Creando sesión para eliminar... "
SESION_DEL_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/sesiones/" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_CREATE")

SESION_DEL_ID=$(echo "$SESION_DEL_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
echo -e "${GREEN}✓${NC} $SESION_DEL_ID"

echo ""

# TC-010: Eliminar sesión
run_test "Eliminar sesión (DELETE /sesiones/{id})" "204" \
    curl -s -w "\n%{http_code}" -X DELETE "$API_URL/api/v1/sesiones/$SESION_DEL_ID"

echo ""

# TC-011: Verificar que la sesión eliminada no existe
run_test "Verificar que sesión eliminada retorna 404" "404" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/sesiones/$SESION_DEL_ID"

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
