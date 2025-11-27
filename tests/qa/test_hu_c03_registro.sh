#!/bin/bash

# Script de pruebas para HU-C03: Cliente nuevo - Registrarme con datos obligatorios
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Módulo: Registro de usuario - Backend
# Fecha: 2025-11-14
# Historia de Usuario: Como cliente nuevo, quiero registrarme con mis datos obligatorios para no reescribir datos en cada visita

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
echo "  HU-C03: Registro de Cliente Nuevo"
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

echo "=== Tests de Registro de Usuario ==="
echo ""

# Email único para cada ejecución
TIMESTAMP=$(date +%s%N | cut -c1-13)
TEST_EMAIL="qa_reg_${TIMESTAMP}@test.com"
TEST_NOMBRE="QA Test User"
TEST_DNI="12345678"

# TC-001: Registro exitoso con campos obligatorios
REGISTRO_PAYLOAD=$(cat <<EOF
{
  "email": "$TEST_EMAIL",
  "nombre": "$TEST_NOMBRE",
  "password": "TestPass123",
  "dni": "$TEST_DNI"
}
EOF
)

# TC-001: Registro exitoso con campos obligatorios
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Registro con campos obligatorios (POST /auth/register)... " >&2

REGISTRO_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "$REGISTRO_PAYLOAD")

status_code=$(echo "$REGISTRO_RESPONSE" | tail -n1)
body=$(echo "$REGISTRO_RESPONSE" | sed '$d')

if [ "$status_code" = "201" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected: 201, Got: $status_code)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "Response body: $body" >&2
fi

USER_ID=$(echo "$body" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

echo ""

# TC-002: Validar que se devuelve ID de usuario
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que registro retorna ID de usuario... " >&2

if [ -n "$USER_ID" ]; then
    echo -e "${GREEN}✓ PASS${NC} (User ID: $USER_ID)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (No se obtuvo ID de usuario)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-003: Intentar registrar mismo email (debe fallar)
run_test "Registro con email duplicado (debe fallar)" "400" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "$REGISTRO_PAYLOAD" > /dev/null

echo ""

# TC-004: Registro sin email (campo obligatorio)
PAYLOAD_SIN_EMAIL=$(cat <<EOF
{
  "nombre": "$TEST_NOMBRE",
  "password": "TestPass123",
  "dni": "$TEST_DNI"
}
EOF
)

run_test "Registro sin email (debe fallar)" "422" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_SIN_EMAIL" > /dev/null

echo ""

# TC-005: Registro sin nombre (campo obligatorio)
PAYLOAD_SIN_NOMBRE=$(cat <<EOF
{
  "email": "otro_$TEST_EMAIL",
  "password": "TestPass123",
  "dni": "$TEST_DNI"
}
EOF
)

run_test "Registro sin nombre (debe fallar)" "422" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_SIN_NOMBRE" > /dev/null

echo ""

# TC-006: Email con formato inválido
PAYLOAD_EMAIL_INVALIDO=$(cat <<EOF
{
  "email": "no-es-un-email",
  "nombre": "$TEST_NOMBRE",
  "password": "TestPass123",
  "dni": "$TEST_DNI"
}
EOF
)

run_test "Registro con email inválido (debe fallar)" "422" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_EMAIL_INVALIDO" > /dev/null

echo ""
echo "=========================================="
echo "  Resumen de Tests - HU-C03"
echo "=========================================="
echo "Historia: Cliente se registra con datos obligatorios"
echo "Backend: Endpoints de registro"
echo ""
echo "Total:  $TOTAL_TESTS"
echo -e "Pasados: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Fallidos: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los tests pasaron${NC}"
    echo ""
    echo "Análisis: El backend provee:"
    echo "  - Registro con campos obligatorios (email, nombre)"
    echo "  - Validación de email duplicado"
    echo "  - Validación de campos obligatorios"
    echo "  - Validación de formato de email"
    exit 0
else
    echo -e "${RED}✗ Algunos tests fallaron${NC}"
    exit 1
fi
