#!/bin/bash

# Script de pruebas para HU-C04: Cliente registrado - Iniciar sesión
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Módulo: Login - Backend
# Fecha: 2025-11-14
# Historia de Usuario: Como cliente registrado, quiero iniciar sesión en mi cuenta para recuperar mi experiencia y pedidos

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
API_URL="${API_URL:-https://back-dp2.onrender.com}"
VERBOSE="${VERBOSE:-false}"

echo "=========================================="
echo "  HU-C04: Login de Cliente"
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

echo "=== Tests de Login por Mesa (Simplificado) ==="
echo ""

# Obtener lista de mesas (skip=1 para usar otra mesa diferente)
MESAS_RESPONSE=$(curl -s "$API_URL/api/v1/mesas?skip=1&limit=1")
MESA_ID=$(echo "$MESAS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

echo "Mesa para test: $MESA_ID"
echo ""

# Email único para test
TIMESTAMP=$(date +%s%N | cut -c1-13)
TEST_EMAIL="qa_login_${TIMESTAMP}@test.com"
TEST_NOMBRE="QA Login Test"

# TC-001: Login exitoso con email y nombre
LOGIN_PAYLOAD=$(cat <<EOF
{
  "email": "$TEST_EMAIL",
  "nombre": "$TEST_NOMBRE"
}
EOF
)

# TC-001: Login exitoso con email y nombre
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Login por mesa (POST /login?id_mesa=...)... " >&2

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/login?id_mesa=$MESA_ID" \
    -H "Content-Type: application/json" \
    -d "$LOGIN_PAYLOAD")
status_code=$(echo "$response" | tail -n1)
LOGIN_RESPONSE=$(echo "$response" | sed '$d')

if [ "$VERBOSE" = "true" ]; then
    echo "" >&2
    echo "Response: $LOGIN_RESPONSE" >&2
    echo "Status: $status_code" >&2
fi

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected: 200, Got: $status_code)" >&2
    echo "Response body: $LOGIN_RESPONSE" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

TOKEN_SESION=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('token_sesion', ''))" 2>/dev/null)
USER_ID=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id_usuario', ''))" 2>/dev/null)

echo ""

# TC-002: Validar que login retorna token_sesion
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que login retorna token_sesion... " >&2

if [ -n "$TOKEN_SESION" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Token: ${TOKEN_SESION:0:20}...)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (No se obtuvo token)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-003: Validar que login retorna id_usuario
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que login retorna id_usuario... " >&2

if [ -n "$USER_ID" ]; then
    echo -e "${GREEN}✓ PASS${NC} (User ID: $USER_ID)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (No se obtuvo user ID)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-004: Login sin email (debe fallar)
PAYLOAD_SIN_EMAIL=$(cat <<EOF
{
  "nombre": "$TEST_NOMBRE"
}
EOF
)

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Login sin email (debe fallar)... " >&2

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/login?id_mesa=$MESA_ID" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_SIN_EMAIL")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$VERBOSE" = "true" ]; then
    echo "" >&2
    echo "Response: $body" >&2
    echo "Status: $status_code" >&2
fi

if [ "$status_code" = "422" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected: 422, Got: $status_code)" >&2
    echo "Response body: $body" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-005: Login sin id_mesa (debe fallar)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Login sin id_mesa en query (debe fallar)... " >&2

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/login" \
    -H "Content-Type: application/json" \
    -d "$LOGIN_PAYLOAD")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$VERBOSE" = "true" ]; then
    echo "" >&2
    echo "Response: $body" >&2
    echo "Status: $status_code" >&2
fi

if [ "$status_code" = "422" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected: 422, Got: $status_code)" >&2
    echo "Response body: $body" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-006: Segundo login con mismo email en misma mesa
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Segundo login mismo email/mesa... " >&2

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/login?id_mesa=$MESA_ID" \
    -H "Content-Type: application/json" \
    -d "$LOGIN_PAYLOAD")
status_code=$(echo "$response" | tail -n1)
SEGUNDO_LOGIN=$(echo "$response" | sed '$d')

if [ "$VERBOSE" = "true" ]; then
    echo "" >&2
    echo "Response: $SEGUNDO_LOGIN" >&2
    echo "Status: $status_code" >&2
fi

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected: 200, Got: $status_code)" >&2
    echo "Response body: $SEGUNDO_LOGIN" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-007: Validar que segundo login retorna datos
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que permite re-login... " >&2

NUEVO_TOKEN=$(echo "$SEGUNDO_LOGIN" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('token_sesion', ''))" 2>/dev/null)

if [ -n "$NUEVO_TOKEN" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Re-login exitoso)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Re-login falló)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=========================================="
echo "  Resumen de Tests - HU-C04"
echo "=========================================="
echo "Historia: Cliente inicia sesión"
echo "Backend: Sistema de login por mesa"
echo ""
echo "Total:  $TOTAL_TESTS"
echo -e "Pasados: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Fallidos: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los tests pasaron${NC}"
    echo ""
    echo "Análisis: El backend provee:"
    echo "  - Login simplificado por mesa (sin password)"
    echo "  - Creación automática de usuario"
    echo "  - Token de sesión para autenticación"
    echo "  - Permite re-login con mismo email"
    exit 0
else
    echo -e "${RED}✗ Algunos tests fallaron${NC}"
    exit 1
fi
