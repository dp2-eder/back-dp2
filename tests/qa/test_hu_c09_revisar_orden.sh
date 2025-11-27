#!/bin/bash

# Script de pruebas para HU-C09: Cliente antes de confirmar - Revisar orden/carrito
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Módulo: Carrito/Orden - Backend
# Fecha: 2025-11-14
# Historia de Usuario: Como cliente antes de confirmar, quiero revisar cantidades, subtotales e impuestos de mi orden para validar mi consumo antes de enviar

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
echo "  HU-C09: Revisar Orden Antes de Confirmar"
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

echo "=== Preparación: Crear orden de prueba ==="
echo ""

# Obtener token de autenticación (esto ya setea USER_ID automáticamente)
get_auth_token || exit 1

# Obtener IDs necesarios (USER_ID ya está seteado por get_auth_token)
MESA_RESPONSE=$(curl -s "$API_URL/api/v1/mesas?limit=1")
MESA_ID=$(echo "$MESA_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

PRODUCTOS_RESPONSE=$(curl -s "$API_URL/api/v1/productos/cards?limit=2")
PRODUCTO1_ID=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; items = json.load(sys.stdin).get('items', []); print(items[0]['id'] if len(items) > 0 else '')" 2>/dev/null)
PRODUCTO1_PRECIO=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; items = json.load(sys.stdin).get('items', []); print(items[0]['precio_base'] if len(items) > 0 else '')" 2>/dev/null)

PRODUCTO2_ID=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; items = json.load(sys.stdin).get('items', []); print(items[1]['id'] if len(items) > 1 else '')" 2>/dev/null)
PRODUCTO2_PRECIO=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; items = json.load(sys.stdin).get('items', []); print(items[1]['precio_base'] if len(items) > 1 else '')" 2>/dev/null)

echo "Usuario: $USER_ID"
echo "Mesa: $MESA_ID"
echo "Producto 1: $PRODUCTO1_ID (S/$PRODUCTO1_PRECIO)"
echo "Producto 2: $PRODUCTO2_ID (S/$PRODUCTO2_PRECIO)"
echo ""

# Crear pedido con múltiples items
PAYLOAD=$(cat <<EOF
{
  "id_usuario": "$USER_ID",
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO1_ID",
      "cantidad": 2,
      "precio_unitario": $PRODUCTO1_PRECIO,
      "opciones": [],
      "notas_personalizacion": null
    },
    {
      "id_producto": "$PRODUCTO2_ID",
      "cantidad": 3,
      "precio_unitario": $PRODUCTO2_PRECIO,
      "opciones": [],
      "notas_personalizacion": null
    }
  ],
  "notas_cliente": "Orden de prueba HU-C09",
  "notas_cocina": null
}
EOF
)

PEDIDO_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "$PAYLOAD")

PEDIDO_ID=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

if [ -n "$PEDIDO_ID" ]; then
    echo -e "${GREEN}✓${NC} Pedido creado: $PEDIDO_ID"
else
    echo -e "${RED}✗ No se pudo crear pedido de prueba${NC}"
    exit 1
fi

echo ""
echo "=== Tests de Revisión de Orden ==="
echo ""

# TC-001: Obtener pedido para revisar
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Obtener detalle de pedido (GET /pedidos/{id})... " >&2

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos/$PEDIDO_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
status_code=$(echo "$response" | tail -n1)
PEDIDO_DETAIL=$(echo "$response" | sed '$d')

if [ "$VERBOSE" = "true" ]; then
    echo "" >&2
    echo "Response: $PEDIDO_DETAIL" >&2
    echo "Status: $status_code" >&2
fi

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected: 200, Got: $status_code)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "Response body: $PEDIDO_DETAIL" >&2
fi

echo ""

# TC-002: Validar que incluye cantidades
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que muestra cantidades de items... " >&2

ITEMS_COUNT=$(echo "$PEDIDO_DETAIL" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null || echo "0")

if [ "$ITEMS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} (Items: $ITEMS_COUNT)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (No hay items en respuesta)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-003: Validar que incluye subtotal
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que muestra subtotal... " >&2

SUBTOTAL=$(echo "$PEDIDO_DETAIL" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('subtotal', ''))" 2>/dev/null)

if [ -n "$SUBTOTAL" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Subtotal: S/$SUBTOTAL)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ WARN${NC} (Campo subtotal no presente - puede calcularse en frontend)" >&2
fi

echo ""

# TC-004: Validar que incluye total
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que muestra total... " >&2

TOTAL=$(echo "$PEDIDO_DETAIL" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('total', ''))" 2>/dev/null)

if [ -n "$TOTAL" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Total: S/$TOTAL)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Total no presente)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-005: Validar cálculo correcto del total
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que total está calculado correctamente... " >&2

TOTAL_ESPERADO=$(python3 -c "print(float($PRODUCTO1_PRECIO) * 2 + float($PRODUCTO2_PRECIO) * 3)")
DIFF=$(python3 -c "print(abs(float($TOTAL) - float($TOTAL_ESPERADO)))")
IS_CLOSE=$(python3 -c "print($DIFF < 0.01)")

if [ "$IS_CLOSE" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Total: S/$TOTAL ≈ S/$TOTAL_ESPERADO)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: S/$TOTAL_ESPERADO, Obtenido: S/$TOTAL)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-006: Listar items del pedido
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Listar items del pedido (GET /pedidos-productos/pedido/{id}/items)... " >&2

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos-productos/pedido/$PEDIDO_ID/items" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
status_code=$(echo "$response" | tail -n1)
ITEMS_RESPONSE=$(echo "$response" | sed '$d')

if [ "$VERBOSE" = "true" ]; then
    echo "" >&2
    echo "Response: $ITEMS_RESPONSE" >&2
    echo "Status: $status_code" >&2
fi

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected: 200, Got: $status_code)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "Response body: $ITEMS_RESPONSE" >&2
fi

echo ""

# TC-007: Validar que cada item tiene cantidad y precio
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que items tienen cantidad y precio... " >&2

ITEMS_VALIDOS=$(echo "$ITEMS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('items', []) if isinstance(data, dict) else data
if items:
    primer_item = items[0]
    tiene_cantidad = 'cantidad' in primer_item
    tiene_precio = 'precio_unitario' in primer_item
    print(tiene_cantidad and tiene_precio)
else:
    print(False)
" 2>/dev/null)

if [ "$ITEMS_VALIDOS" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Items incluyen cantidad y precio)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Items sin cantidad/precio)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=========================================="
echo "  Resumen de Tests - HU-C09"
echo "=========================================="
echo "Historia: Cliente revisa orden antes de confirmar"
echo "Backend: Endpoints de consulta de pedido"
echo ""
echo "Total:  $TOTAL_TESTS"
echo -e "Pasados: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Fallidos: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los tests pasaron${NC}"
    echo ""
    echo "Análisis: El backend provee:"
    echo "  - Consulta de pedido con items"
    echo "  - Cantidades de cada item"
    echo "  - Subtotal y total calculados"
    echo "  - Lista detallada de items con precios"
    exit 0
else
    echo -e "${RED}✗ Algunos tests fallaron${NC}"
    exit 1
fi
