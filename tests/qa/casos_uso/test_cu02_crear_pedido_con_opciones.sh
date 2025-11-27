#!/bin/bash

# Script de pruebas para Caso de Uso 2: Crear pedido completo con opciones
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

echo "=========================================="
echo "  CU-02: Crear Pedido con Opciones"
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
    echo -n "TC-$TOTAL_TESTS: $test_name... "

    response=$("$@")
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$VERBOSE" = "true" ]; then
        echo ""
        echo "Response: $body"
        echo "Status: $status_code"
    fi

    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Status: $status_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "$body"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: $expected_status, Got: $status_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        if [ "$VERBOSE" = "true" ]; then
            echo "Response body: $body"
        fi
        echo "$body"
        return 1
    fi
}

echo "=== Preparación: Obtener IDs necesarios ==="
echo ""

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

# Obtener un producto con opciones
echo -n "Buscando producto con opciones... "
PRODUCTO_RESPONSE=$(curl -s "$API_URL/api/v1/productos/cards?limit=10")
PRODUCTO_ID=$(echo "$PRODUCTO_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data.get('items', []):
    if item.get('id'):
        print(item['id'])
        break
" 2>/dev/null)

if [ -z "$PRODUCTO_ID" ]; then
    echo -e "${RED}✗ No se encontraron productos${NC}"
    exit 1
fi

# Obtener opciones del producto
PRODUCTO_OPC_RESPONSE=$(curl -s "$API_URL/api/v1/productos/$PRODUCTO_ID/opciones")
PRODUCTO_PRECIO=$(echo "$PRODUCTO_OPC_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('precio_base', 0))" 2>/dev/null)
PRODUCTO_NOMBRE=$(echo "$PRODUCTO_OPC_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('nombre', ''))" 2>/dev/null)

# Obtener IDs de opciones (hasta 2)
OPCION_IDS=$(echo "$PRODUCTO_OPC_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
opciones = data.get('opciones', [])
for i, opc in enumerate(opciones[:2]):
    print(f\"{opc['id']}|{opc.get('precio_adicional', 0)}\")
" 2>/dev/null)

if [ -n "$PRODUCTO_ID" ] && [ -n "$OPCION_IDS" ]; then
    echo -e "${GREEN}✓${NC} Producto: $PRODUCTO_NOMBRE (ID: $PRODUCTO_ID, Precio: S/$PRODUCTO_PRECIO)"
    echo "Opciones encontradas:"
    echo "$OPCION_IDS" | while read line; do
        OPC_ID=$(echo "$line" | cut -d'|' -f1)
        OPC_PRECIO=$(echo "$line" | cut -d'|' -f2)
        echo "  - Opción ID: $OPC_ID (Precio adicional: S/$OPC_PRECIO)"
    done
else
    echo -e "${RED}✗ No se encontraron opciones para productos${NC}"
    exit 1
fi

# Extraer datos de opciones para el payload
OPCION1_ID=$(echo "$OPCION_IDS" | sed -n '1p' | cut -d'|' -f1)
OPCION1_PRECIO=$(echo "$OPCION_IDS" | sed -n '1p' | cut -d'|' -f2)
OPCION2_ID=$(echo "$OPCION_IDS" | sed -n '2p' | cut -d'|' -f1)
OPCION2_PRECIO=$(echo "$OPCION_IDS" | sed -n '2p' | cut -d'|' -f2)

echo ""
echo "=== Tests de Creación de Pedido con Opciones ==="
echo ""

# TC-001: Crear pedido con 1 item con opciones
PAYLOAD=$(cat <<EOF
{
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO_ID",
      "cantidad": 2,
      "precio_unitario": $PRODUCTO_PRECIO,
      "opciones": [
        {
          "id_producto_opcion": "$OPCION1_ID",
          "precio_adicional": $OPCION1_PRECIO
        },
        {
          "id_producto_opcion": "$OPCION2_ID",
          "precio_adicional": $OPCION2_PRECIO
        }
      ],
      "notas_personalizacion": "Test con opciones"
    }
  ],
  "notas_cliente": "Test pedido con opciones",
  "notas_cocina": "Verificar opciones"
}
EOF
)

PEDIDO_RESPONSE=$(run_test "Crear pedido con opciones (2 opciones)" "201" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

PEDIDO_ID=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

echo ""

# TC-002: Validar que el item tiene precio_opciones calculado
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar cálculo de precio_opciones... "
ITEM_PRECIO_OPCIONES=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0].get('precio_opciones', -1) if data.get('items') else -1)" 2>/dev/null)
PRECIO_OPC_ESPERADO=$(python3 -c "print($OPCION1_PRECIO + $OPCION2_PRECIO)")

if [ "$ITEM_PRECIO_OPCIONES" = "$PRECIO_OPC_ESPERADO" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Precio opciones: S/$ITEM_PRECIO_OPCIONES)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: S/$PRECIO_OPC_ESPERADO, Obtenido: S/$ITEM_PRECIO_OPCIONES)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-003: Validar que el item tiene opciones en la respuesta
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que item contiene opciones... "
OPCIONES_COUNT=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data['items'][0].get('opciones', [])) if data.get('items') else 0)" 2>/dev/null)

if [ "$OPCIONES_COUNT" = "2" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Opciones en item: $OPCIONES_COUNT)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: 2 opciones, Obtenido: $OPCIONES_COUNT)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-004: Validar cálculo de subtotal del item (cantidad * (precio_unitario + precio_opciones))
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar cálculo de subtotal del item... "
ITEM_SUBTOTAL=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0].get('subtotal', -1) if data.get('items') else -1)" 2>/dev/null)
SUBTOTAL_ESPERADO=$(python3 -c "print(2 * ($PRODUCTO_PRECIO + $PRECIO_OPC_ESPERADO))")

if [ "$ITEM_SUBTOTAL" = "$SUBTOTAL_ESPERADO" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Subtotal: S/$ITEM_SUBTOTAL)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: S/$SUBTOTAL_ESPERADO, Obtenido: S/$ITEM_SUBTOTAL)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-005: Validar que el subtotal del pedido coincide con suma de items
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar subtotal del pedido... "
PEDIDO_SUBTOTAL=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('subtotal', -1))" 2>/dev/null)

if [ "$PEDIDO_SUBTOTAL" = "$SUBTOTAL_ESPERADO" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Subtotal pedido: S/$PEDIDO_SUBTOTAL)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: S/$SUBTOTAL_ESPERADO, Obtenido: S/$PEDIDO_SUBTOTAL)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-006: Validar estructura de las opciones dentro del item
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar estructura de opciones del item... "
OPCION1_TIENE_ID=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print('id' in data['items'][0]['opciones'][0] if data.get('items') and data['items'][0].get('opciones') else False)" 2>/dev/null)
OPCION1_TIENE_PRECIO=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print('precio_adicional' in data['items'][0]['opciones'][0] if data.get('items') and data['items'][0].get('opciones') else False)" 2>/dev/null)

if [ "$OPCION1_TIENE_ID" = "True" ] && [ "$OPCION1_TIENE_PRECIO" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Campos: id, precio_adicional presentes)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Estructura incompleta)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-007: Validar notas de personalización
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar notas de personalización del item... "
NOTAS_PERSONALIZACION=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0].get('notas_personalizacion', '') if data.get('items') else '')" 2>/dev/null)

if [ "$NOTAS_PERSONALIZACION" = "Test con opciones" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Notas: $NOTAS_PERSONALIZACION)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Notas incorrectas)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=== Test de Pedido con Múltiples Items ==="
echo ""

# TC-008: Crear pedido con múltiples items y opciones
PAYLOAD_MULTI=$(cat <<EOF
{
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO_ID",
      "cantidad": 1,
      "precio_unitario": $PRODUCTO_PRECIO,
      "opciones": [
        {
          "id_producto_opcion": "$OPCION1_ID",
          "precio_adicional": $OPCION1_PRECIO
        }
      ],
      "notas_personalizacion": "Item 1"
    },
    {
      "id_producto": "$PRODUCTO_ID",
      "cantidad": 2,
      "precio_unitario": $PRODUCTO_PRECIO,
      "opciones": [],
      "notas_personalizacion": "Item 2 sin opciones"
    }
  ],
  "notas_cliente": "Test múltiples items",
  "notas_cocina": null
}
EOF
)

PEDIDO_MULTI_RESPONSE=$(run_test "Crear pedido con múltiples items (2 items)" "201" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_MULTI")

echo ""

# TC-009: Validar que el pedido tiene 2 items
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que pedido tiene 2 items... "
ITEMS_COUNT=$(echo "$PEDIDO_MULTI_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null)

if [ "$ITEMS_COUNT" = "2" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Items: $ITEMS_COUNT)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: 2, Obtenido: $ITEMS_COUNT)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-010: Validar que el subtotal total suma correctamente ambos items
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar subtotal total de múltiples items... "
SUBTOTAL_MULTI=$(echo "$PEDIDO_MULTI_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('subtotal', -1))" 2>/dev/null)
# Item 1: 1 * (precio + opcion1)
# Item 2: 2 * (precio + 0)
SUBTOTAL_MULTI_ESPERADO=$(python3 -c "print(1 * ($PRODUCTO_PRECIO + $OPCION1_PRECIO) + 2 * $PRODUCTO_PRECIO)")

if [ "$SUBTOTAL_MULTI" = "$SUBTOTAL_MULTI_ESPERADO" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Subtotal: S/$SUBTOTAL_MULTI)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: S/$SUBTOTAL_MULTI_ESPERADO, Obtenido: S/$SUBTOTAL_MULTI)"
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
