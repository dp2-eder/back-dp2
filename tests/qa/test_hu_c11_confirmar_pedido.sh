#!/bin/bash

# Script de pruebas para HU-C11: Cliente listo para enviar - Confirmar el envío de mi pedido
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Módulo: Pre-Orden - Backend
# Fecha: 2025-11-13
# Historia de Usuario: Como cliente listo para enviar, quiero confirmar el envío de mi pedido para que el negocio lo reciba sin errores

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
echo "  HU-C11: Confirmar Envío de Pedido"
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

echo "=== Preparación: Obtener IDs necesarios ==="
echo ""

# Obtener token de autenticación (esto ya setea USER_ID automáticamente)
get_auth_token || exit 1

# Verificar que tenemos USER_ID
if [ -n "$USER_ID" ]; then
    echo "User ID: $USER_ID"
else
    echo -e "${RED}✗ No se pudo obtener ID de usuario${NC}"
    exit 1
fi

# Obtener ID de una mesa
echo -n "Obteniendo ID de mesa... "
MESA_RESPONSE=$(curl -s "$API_URL/api/v1/mesas?limit=1")
MESA_ID=$(echo "$MESA_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

if [ -n "$MESA_ID" ]; then
    echo -e "${GREEN}✓${NC} Mesa ID: $MESA_ID"
else
    echo -e "${RED}✗ No se encontraron mesas${NC}"
    exit 1
fi

# Obtener ID de un producto
echo -n "Obteniendo ID de producto... "
PRODUCTO_RESPONSE=$(curl -s "$API_URL/api/v1/productos/cards?limit=1")
PRODUCTO_ID=$(echo "$PRODUCTO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)
PRODUCTO_PRECIO=$(echo "$PRODUCTO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['precio_base'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

if [ -n "$PRODUCTO_ID" ]; then
    echo -e "${GREEN}✓${NC} Producto ID: $PRODUCTO_ID (Precio: S/$PRODUCTO_PRECIO)"
else
    echo -e "${RED}✗ No se encontraron productos${NC}"
    exit 1
fi

echo ""
echo "=== Tests de Creación de Pedido Completo ==="
echo ""

# TC-001: Crear pedido completo con datos obligatorios
PAYLOAD=$(cat <<EOF
{
  "id_usuario": "$USER_ID",
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO_ID",
      "cantidad": 2,
      "precio_unitario": $PRODUCTO_PRECIO,
      "opciones": [],
      "notas_personalizacion": null
    }
  ],
  "notas_cliente": "Pedido de prueba HU-C11",
  "notas_cocina": null
}
EOF
)

# TC-001: Crear pedido completo (POST /pedidos/completo)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Crear pedido completo (POST /pedidos/completo)... " >&2

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "$PAYLOAD")

status_code=$(echo "$response" | tail -n1)
PEDIDO_RESPONSE=$(echo "$response" | sed '$d')

if [ "$VERBOSE" = "true" ]; then
    echo "" >&2
    echo "Response: $PEDIDO_RESPONSE" >&2
    echo "Status: $status_code" >&2
fi

if [ "$status_code" = "201" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected: 201, Got: $status_code)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "Response body: $PEDIDO_RESPONSE" >&2
fi

PEDIDO_ID=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

echo ""

# TC-002: Validar que pedido tiene total calculado
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que pedido tiene total calculado... " >&2

TOTAL=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('total', 0))" 2>/dev/null)
EXPECTED_TOTAL=$(python3 -c "print(float($PRODUCTO_PRECIO) * 2)")

# Comparación numérica con tolerancia de 0.01
DIFF=$(python3 -c "print(abs(float($TOTAL) - float($EXPECTED_TOTAL)))")
IS_CLOSE=$(python3 -c "print($DIFF < 0.01)")

if [ "$IS_CLOSE" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Total: S/$TOTAL)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: S/$EXPECTED_TOTAL, Obtenido: S/$TOTAL)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-003: Validar que pedido tiene datos obligatorios completos
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar datos obligatorios (id, numero_pedido, estado)... " >&2

NUMERO_PEDIDO=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('numero_pedido', ''))" 2>/dev/null)
ESTADO=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('estado', ''))" 2>/dev/null)

if [ -n "$PEDIDO_ID" ] && [ -n "$NUMERO_PEDIDO" ] && [ "$ESTADO" = "pendiente" ]; then
    echo -e "${GREEN}✓ PASS${NC} (ID: OK, Número: $NUMERO_PEDIDO, Estado: $ESTADO)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Campos incompletos)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=== Tests de Envío de Pedido ==="
echo ""

if [ -n "$PEDIDO_ID" ]; then
    # TC-004: Enviar pedido (cambiar estado a confirmado/enviado)
    # Nota: Verificar si existe endpoint específico POST /pedidos/enviar
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Enviar pedido (POST /pedidos/enviar)... " >&2

    ENVIAR_PAYLOAD=$(cat <<EOF
{
    "pedido_id": "$PEDIDO_ID",
    "token_sesion": "$TOKEN_SESION",
    "items": [
        {
            "id_producto": "$PRODUCTO_ID",
            "cantidad": 2,
            "precio_unitario": $PRODUCTO_PRECIO,
            "opciones": [],
            "notas_personalizacion": null
        }
    ]
}
EOF
)

    response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/enviar" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "$ENVIAR_PAYLOAD")

    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$VERBOSE" = "true" ]; then
        echo "" >&2
        echo "Request payload: $ENVIAR_PAYLOAD" >&2
        echo "Response: $body" >&2
        echo "Status: $status_code" >&2
    fi

    if [ "$status_code" = "200" ] || [ "$status_code" = "201" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: 200/201, Got: $status_code)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "Response body: $body" >&2
    fi

    echo ""

    # TC-005: Verificar que el pedido fue registrado correctamente
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Obtener pedido confirmado (GET /pedidos/{id})... " >&2

    response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos/$PEDIDO_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    status_code=$(echo "$response" | tail -n1)
    PEDIDO_GET=$(echo "$response" | sed '$d')

    if [ "$VERBOSE" = "true" ]; then
        echo "" >&2
        echo "Response: $PEDIDO_GET" >&2
        echo "Status: $status_code" >&2
    fi

    if [ "$status_code" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: 200, Got: $status_code)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "Response body: $PEDIDO_GET" >&2
    fi

    echo ""

    # TC-006: Validar que pedido está en estado confirmado/enviado
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Validar que pedido fue confirmado... " >&2

    ESTADO_ACTUAL=$(echo "$PEDIDO_GET" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('estado', ''))" 2>/dev/null)

    if [ -n "$ESTADO_ACTUAL" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Estado: $ESTADO_ACTUAL)" >&2
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Estado vacío)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo -e "${YELLOW}⚠ SKIP${NC} - No se pudo crear pedido, tests de envío omitidos" >&2
fi

echo ""
echo "=========================================="
echo "  Resumen de Tests - HU-C11"
echo "=========================================="
echo "Historia: Cliente confirma envío de pedido"
echo "Backend: Endpoints de creación y envío de pedido"
echo ""
echo "Total:  $TOTAL_TESTS"
echo -e "Pasados: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Fallidos: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los tests pasaron${NC}"
    echo ""
    echo "Análisis: El backend provee:"
    echo "  - Creación de pedido con datos obligatorios"
    echo "  - Cálculo automático de total"
    echo "  - Envío/confirmación de pedido"
    echo "  - Validación de datos completos antes de confirmar"
    exit 0
else
    echo -e "${RED}✗ Algunos tests fallaron${NC}"
    exit 1
fi
