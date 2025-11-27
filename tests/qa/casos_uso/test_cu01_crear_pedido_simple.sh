#!/bin/bash

# Script de pruebas para Caso de Uso 1: Crear pedido completo simple
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Modulo: Pedidos - Backend
# Fecha: 2025-10-29

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
echo "  CU-01: Crear Pedido Completo Simple"
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

echo "=== Preparación: Obtener IDs necesarios ==="
echo ""

# Obtener token de autenticación
get_auth_token || exit 1

# Obtener ID de usuario del token
echo -n "Obteniendo ID de usuario... "
USER_RESPONSE=$(curl -s "$API_URL/api/v1/auth/me" -H "Authorization: Bearer $ACCESS_TOKEN")
USER_ID=$(echo "$USER_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

if [ -n "$USER_ID" ]; then
    echo -e "${GREEN}✓${NC} User ID: $USER_ID"
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
PRODUCTO_NOMBRE=$(echo "$PRODUCTO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['nombre'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

if [ -n "$PRODUCTO_ID" ]; then
    echo -e "${GREEN}✓${NC} Producto: $PRODUCTO_NOMBRE (ID: $PRODUCTO_ID, Precio: S/$PRODUCTO_PRECIO)"
else
    echo -e "${RED}✗ No se encontraron productos${NC}"
    exit 1
fi

echo ""
echo "=== Tests de Creación de Pedido Simple ==="
echo ""

# TC-001: Crear pedido simple con 1 item sin opciones
PAYLOAD=$(cat <<EOF
{
  "id_usuario": "$USER_ID",
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO_ID",
      "cantidad": 1,
      "precio_unitario": $PRODUCTO_PRECIO,
      "opciones": [],
      "notas_personalizacion": null
    }
  ],
  "notas_cliente": "Test pedido simple",
  "notas_cocina": null
}
EOF
)

PEDIDO_RESPONSE=$(run_test "Crear pedido simple (1 item, sin opciones)" "201" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "$PAYLOAD")

PEDIDO_ID=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

echo ""

# TC-002: Validar que el pedido tiene ID generado
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que pedido tiene ID generado (ULID)... "
if [ -n "$PEDIDO_ID" ] && [ ${#PEDIDO_ID} -eq 26 ]; then
    echo -e "${GREEN}✓ PASS${NC} (ID: $PEDIDO_ID)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (ID inválido o vacío)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-003: Validar que el pedido tiene numero_pedido generado
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que pedido tiene numero_pedido generado... "
NUMERO_PEDIDO=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('numero_pedido', ''))" 2>/dev/null)
if [ -n "$NUMERO_PEDIDO" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Número: $NUMERO_PEDIDO)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Número de pedido vacío)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-004: Validar estado inicial es pendiente
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que estado inicial es pendiente... "
ESTADO=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('estado', ''))" 2>/dev/null)
if [ "$ESTADO" = "pendiente" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Estado: $ESTADO)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Estado esperado: pendiente, obtenido: $ESTADO)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-005: Validar cálculo de subtotal
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar cálculo correcto de subtotal... "
SUBTOTAL=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('subtotal', 0))" 2>/dev/null)
if [ "$SUBTOTAL" = "$PRODUCTO_PRECIO" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Subtotal: S/$SUBTOTAL)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: S/$PRODUCTO_PRECIO, Obtenido: S/$SUBTOTAL)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-006: Validar que total = subtotal (sin impuestos ni descuentos)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que total = subtotal... "
TOTAL=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('total', 0))" 2>/dev/null)
if [ "$TOTAL" = "$SUBTOTAL" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Total: S/$TOTAL)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Total: S/$TOTAL != Subtotal: S/$SUBTOTAL)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-007: Validar que el pedido tiene items
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que pedido contiene items... "
ITEMS_COUNT=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null)
if [ "$ITEMS_COUNT" = "1" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Items: $ITEMS_COUNT)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: 1 item, Obtenido: $ITEMS_COUNT)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-008: Validar estructura del item
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar estructura completa del item... "
ITEM_ID=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0].get('id', '') if data.get('items') else '')" 2>/dev/null)
ITEM_CANTIDAD=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0].get('cantidad', 0) if data.get('items') else 0)" 2>/dev/null)
ITEM_PRECIO_OPCIONES=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0].get('precio_opciones', -1) if data.get('items') else -1)" 2>/dev/null)
ITEM_ID_PRODUCTO=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0].get('id_producto', '') if data.get('items') else '')" 2>/dev/null)

# Validar cada campo
ERRORS=""
if [ -z "$ITEM_ID" ]; then ERRORS="${ERRORS}item.id vacío; "; fi
if [ "$ITEM_CANTIDAD" != "1" ]; then ERRORS="${ERRORS}cantidad=$ITEM_CANTIDAD (esperado: 1); "; fi
if [ -z "$ITEM_ID_PRODUCTO" ]; then ERRORS="${ERRORS}id_producto vacío; "; fi
if [ "$ITEM_PRECIO_OPCIONES" != "0.0" ] && [ "$ITEM_PRECIO_OPCIONES" != "0.00" ]; then ERRORS="${ERRORS}precio_opciones=$ITEM_PRECIO_OPCIONES (esperado: 0.00); "; fi

if [ -z "$ERRORS" ]; then
    echo -e "${GREEN}✓ PASS${NC} (ID: OK, Cantidad: $ITEM_CANTIDAD, Precio opciones: S/$ITEM_PRECIO_OPCIONES)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Errores: $ERRORS"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=== Tests de Consulta del Pedido Creado ==="
echo ""

if [ -n "$PEDIDO_ID" ]; then
    # TC-009: Obtener pedido por ID
    PEDIDO_GET=$(run_test "Obtener pedido por ID (GET /pedidos/{id})" "200" \
        curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos/$PEDIDO_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    # TC-010: Obtener pedido por número
    if [ -n "$NUMERO_PEDIDO" ]; then
        run_test "Obtener pedido por número (GET /pedidos/numero/{numero})" "200" \
            curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos/numero/$NUMERO_PEDIDO" \
            -H "Authorization: Bearer $ACCESS_TOKEN"
    fi
else
    echo -e "${YELLOW}⚠ SKIP${NC} - No se pudo crear pedido, tests de consulta omitidos"
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
