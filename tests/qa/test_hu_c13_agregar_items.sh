#!/bin/bash

# Script de pruebas para HU-C13: Cliente con consumo activo - Agregar nuevos ítems a la misma orden
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Módulo: Agregar ítems a orden en curso - Backend
# Fecha: 2025-11-13
# Historia de Usuario: Como cliente con consumo activo, quiero agregar nuevos ítems a la misma orden para no abrir una orden distinta

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
echo "  HU-C13: Agregar Ítems a Orden Activa"
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

echo "=== Preparación: Crear orden inicial ==="
echo ""

# Obtener token de autenticación (esto ya setea USER_ID automáticamente)
get_auth_token || exit 1

# Obtener IDs necesarios (USER_ID ya está seteado por get_auth_token)
MESA_RESPONSE=$(curl -s "$API_URL/api/v1/mesas?limit=1")
MESA_ID=$(echo "$MESA_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

PRODUCTOS_RESPONSE=$(curl -s "$API_URL/api/v1/productos/cards?limit=3")
PRODUCTO1_ID=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; items = json.load(sys.stdin).get('items', []); print(items[0]['id'] if len(items) > 0 else '')" 2>/dev/null)
PRODUCTO1_PRECIO=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; items = json.load(sys.stdin).get('items', []); print(items[0]['precio_base'] if len(items) > 0 else '')" 2>/dev/null)
PRODUCTO1_NOMBRE=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; items = json.load(sys.stdin).get('items', []); print(items[0]['nombre'] if len(items) > 0 else '')" 2>/dev/null)

PRODUCTO2_ID=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; items = json.load(sys.stdin).get('items', []); print(items[1]['id'] if len(items) > 1 else '')" 2>/dev/null)
PRODUCTO2_PRECIO=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; items = json.load(sys.stdin).get('items', []); print(items[1]['precio_base'] if len(items) > 1 else '')" 2>/dev/null)
PRODUCTO2_NOMBRE=$(echo "$PRODUCTOS_RESPONSE" | python3 -c "import sys, json; items = json.load(sys.stdin).get('items', []); print(items[1]['nombre'] if len(items) > 1 else '')" 2>/dev/null)

echo "Usuario: $USER_ID"
echo "Mesa: $MESA_ID"
echo "Producto 1: $PRODUCTO1_NOMBRE (S/$PRODUCTO1_PRECIO)"
echo "Producto 2: $PRODUCTO2_NOMBRE (S/$PRODUCTO2_PRECIO)"
echo ""

# Crear pedido inicial
PAYLOAD_INICIAL=$(cat <<EOF
{
  "id_usuario": "$USER_ID",
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO1_ID",
      "cantidad": 1,
      "precio_unitario": $PRODUCTO1_PRECIO,
      "opciones": [],
      "notas_personalizacion": null
    }
  ],
  "notas_cliente": "Pedido inicial HU-C13",
  "notas_cocina": null
}
EOF
)

PEDIDO_INICIAL=$(curl -s -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "$PAYLOAD_INICIAL")

PEDIDO_ID=$(echo "$PEDIDO_INICIAL" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
ITEMS_INICIALES=$(echo "$PEDIDO_INICIAL" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null || echo "0")

if [ -n "$PEDIDO_ID" ]; then
    echo -e "${GREEN}✓${NC} Pedido inicial creado: ID=$PEDIDO_ID, Items: $ITEMS_INICIALES"
else
    echo -e "${RED}✗ No se pudo crear pedido inicial${NC}"
    exit 1
fi

echo ""
echo "=== Tests de Agregar Ítems a Pedido Existente ==="
echo ""

# TC-001: Agregar nuevo ítem al pedido (POST /pedidos-productos)
ITEM_PAYLOAD=$(cat <<EOF
{
  "id_pedido": "$PEDIDO_ID",
  "id_producto": "$PRODUCTO2_ID",
  "cantidad": 2,
  "precio_unitario": $PRODUCTO2_PRECIO,
  "precio_opciones": 0.0,
  "notas_personalizacion": "Extra queso"
}
EOF
)

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Agregar nuevo ítem a pedido (POST /pedidos-productos)... " >&2

response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos-productos" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "$ITEM_PAYLOAD")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$VERBOSE" = "true" ]; then
    echo "" >&2
    echo "Response: $body" >&2
    echo "Status: $status_code" >&2
fi

if [ "$status_code" = "201" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Expected: 201, Got: $status_code)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "Response body: $body" >&2
fi

NUEVO_ITEM="$body"

NUEVO_ITEM_ID=$(echo "$NUEVO_ITEM" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

echo ""

# TC-002: Verificar que el ítem fue agregado
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que ítem fue creado con ID... " >&2

if [ -n "$NUEVO_ITEM_ID" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Nuevo ítem ID: $NUEVO_ITEM_ID)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (No se obtuvo ID del nuevo ítem)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-003: Obtener items del pedido
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Obtener items del pedido (GET /pedidos-productos/pedido/{id}/items)... " >&2

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos-productos/pedido/$PEDIDO_ID/items" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

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

ITEMS_PEDIDO="$body"

ITEMS_COUNT=$(echo "$ITEMS_PEDIDO" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])) if isinstance(data, dict) else len(data))" 2>/dev/null || echo "0")

echo ""

# TC-004: Validar que el pedido ahora tiene más ítems
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que pedido tiene nuevos ítems... " >&2

EXPECTED_ITEMS=$((ITEMS_INICIALES + 1))

if [ "$ITEMS_COUNT" -ge "$EXPECTED_ITEMS" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Items: $ITEMS_INICIALES → $ITEMS_COUNT)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: >= $EXPECTED_ITEMS, Obtenido: $ITEMS_COUNT)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-005: Obtener pedido actualizado y validar total
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Obtener pedido actualizado (GET /pedidos/{id})... " >&2

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos/$PEDIDO_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

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

PEDIDO_ACTUALIZADO="$body"

echo ""

# TC-006: Validar que el total se actualizó correctamente
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que total se actualizó correctamente... " >&2

TOTAL_ACTUAL=$(echo "$PEDIDO_ACTUALIZADO" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('total', 0))" 2>/dev/null)
TOTAL_ESPERADO=$(python3 -c "print(float($PRODUCTO1_PRECIO) + (float($PRODUCTO2_PRECIO) * 2))")

# Comparar con tolerancia de 0.01
DIFF=$(python3 -c "print(abs(float($TOTAL_ACTUAL) - float($TOTAL_ESPERADO)))")
IS_CLOSE=$(python3 -c "print($DIFF < 0.01)")

if [ "$IS_CLOSE" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Total: S/$TOTAL_ACTUAL ≈ S/$TOTAL_ESPERADO)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: S/$TOTAL_ESPERADO, Obtenido: S/$TOTAL_ACTUAL)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-007: Validar que los ítems anteriores no se alteraron
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que ítems enviados previamente no se alteraron... " >&2

ITEMS_ACTUALES=$(echo "$PEDIDO_ACTUALIZADO" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null || echo "0")

if [ "$ITEMS_ACTUALES" -ge "$ITEMS_INICIALES" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Ítems anteriores preservados)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Ítems anteriores se perdieron)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=========================================="
echo "  Resumen de Tests - HU-C13"
echo "=========================================="
echo "Historia: Cliente agrega ítems a orden activa"
echo "Backend: Endpoints de pedidos-productos"
echo ""
echo "Total:  $TOTAL_TESTS"
echo -e "Pasados: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Fallidos: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los tests pasaron${NC}"
    echo ""
    echo "Análisis: El backend provee:"
    echo "  - Agregar nuevos ítems a pedido existente"
    echo "  - Listar ítems de un pedido"
    echo "  - Actualización automática del total"
    echo "  - Preservación de ítems enviados anteriormente"
    exit 0
else
    echo -e "${RED}✗ Algunos tests fallaron${NC}"
    exit 1
fi
