#!/bin/bash

# Script de pruebas para HU-C01: Cliente en mesa - Acceso mediante QR
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Módulo: Mesas - Backend
# Fecha: 2025-11-13
# Historia de Usuario: Como cliente en mesa, quiero ordenar por mi cuenta sin llamar al mesero

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
echo "  HU-C01: Acceso mediante QR a Mesa"
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

    # Ejecutar comando pasado como argumentos restantes
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

echo "=== Tests de Acceso a Mesa ==="
echo ""

# TC-001: Obtener lista de mesas disponibles
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Obtener lista de mesas (GET /mesas)... " >&2

MESAS_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/mesas?limit=10")
status_code=$(echo "$MESAS_RESPONSE" | tail -n1)
body=$(echo "$MESAS_RESPONSE" | sed '$d')

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

MESA_COUNT=$(echo "$body" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null || echo "0")

echo ""

# TC-002: Validar que existen mesas
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que existen mesas en el sistema... " >&2
if [ "$MESA_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} (Mesas encontradas: $MESA_COUNT)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (No hay mesas en el sistema)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Obtener ID de una mesa para tests posteriores
MESA_ID=$(echo "$body" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

if [ -n "$MESA_ID" ]; then
    echo ""
    # TC-003: Obtener información de una mesa específica por ID
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Obtener detalle de mesa por ID (GET /mesas/{id})... " >&2

    MESA_DETAIL=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/mesas/$MESA_ID")
    status_code=$(echo "$MESA_DETAIL" | tail -n1)
    body=$(echo "$MESA_DETAIL" | sed '$d')

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

    echo ""

    # TC-004: Validar que mesa tiene campos obligatorios
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Validar campos obligatorios de mesa... " >&2
    MESA_NUMERO=$(echo "$body" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('numero', ''))" 2>/dev/null)
    MESA_ID_VALID=$(echo "$body" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

    if [ -n "$MESA_NUMERO" ] && [ -n "$MESA_ID_VALID" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Mesa #$MESA_NUMERO, ID: $MESA_ID_VALID)" >&2
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Campos faltantes: numero o id)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    echo ""

    # TC-005: Obtener local asociado a la mesa (para validar que QR lleva a carta correcta)
    run_test "Obtener local asociado a mesa (GET /mesas/{id}/local)" "200" \
        curl -s -w "\n%{http_code}" "$API_URL/api/v1/mesas/$MESA_ID/local" > /dev/null
else
    echo -e "${YELLOW}⚠ SKIP${NC} - No se encontró mesa para tests detallados"
fi

echo ""
echo "=== Tests de QR (Validación de existencia de URLs) ==="
echo ""

# TC-006: Verificar endpoint de URLs de QR
run_test "Obtener URLs de QR para mesas (GET /mesas/qr/urls)" "200" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/mesas/qr/urls"

echo ""
echo "=========================================="
echo "  Resumen de Tests - HU-C01"
echo "=========================================="
echo "Historia: Cliente en mesa quiere ordenar por QR"
echo "Backend: Endpoints de mesas y asociación"
echo ""
echo "Total:  $TOTAL_TESTS"
echo -e "Pasados: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Fallidos: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los tests pasaron${NC}"
    echo ""
    echo "Análisis: El backend tiene los endpoints necesarios para:"
    echo "  - Listar mesas disponibles"
    echo "  - Obtener detalle de mesa por ID"
    echo "  - Obtener local asociado a mesa"
    echo "  - Generar URLs de QR"
    exit 0
else
    echo -e "${RED}✗ Algunos tests fallaron${NC}"
    exit 1
fi
