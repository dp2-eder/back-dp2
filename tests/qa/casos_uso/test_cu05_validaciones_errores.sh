#!/bin/bash

# Script de pruebas para Caso de Uso 5: Validaciones y errores
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Modulo: Pedidos - Backend
# Fecha: 2025-10-29

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_URL="${API_URL:-https://back-dp2.onrender.com}"
VERBOSE="${VERBOSE:-false}"

echo "=========================================="
echo "  CU-05: Validaciones y Errores"
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
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: $expected_status, Got: $status_code)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
        if [ "$VERBOSE" = "true" ]; then
            echo "Response: $body"
        fi
        return 1
    fi
}

echo "=== Tests de Validación de Mesa ==="
echo ""

# TC-001: Crear pedido con mesa inexistente (ID inválido)
PAYLOAD_MESA_INVALIDA=$(cat <<EOF
{
  "id_mesa": "01INVALID000000000000000000",
  "items": [
    {
      "id_producto": "01JTEST0000000000000000000",
      "cantidad": 1,
      "precio_unitario": 25.50,
      "opciones": []
    }
  ]
}
EOF
)

run_test "Mesa inexistente debe retornar 400" "400" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_MESA_INVALIDA"

# TC-002: Crear pedido con mesa vacía
PAYLOAD_MESA_VACIA=$(cat <<EOF
{
  "id_mesa": "",
  "items": [
    {
      "id_producto": "01JTEST0000000000000000000",
      "cantidad": 1,
      "precio_unitario": 25.50,
      "opciones": []
    }
  ]
}
EOF
)

run_test "Mesa vacía debe retornar 400 o 422" "422" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_MESA_VACIA"

echo ""
echo "=== Tests de Validación de Productos ==="
echo ""

# Obtener mesa válida para tests
MESA_ID=$(curl -s "$API_URL/api/v1/mesas?limit=1" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

# TC-003: Crear pedido con producto inexistente
PAYLOAD_PRODUCTO_INVALIDO=$(cat <<EOF
{
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "01INVALID000000000000000000",
      "cantidad": 1,
      "precio_unitario": 25.50,
      "opciones": []
    }
  ]
}
EOF
)

run_test "Producto inexistente debe retornar 400" "400" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_PRODUCTO_INVALIDO"

# Obtener producto válido
PRODUCTO_ID=$(curl -s "$API_URL/api/v1/productos/cards?limit=1" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') else '')" 2>/dev/null)

echo ""
echo "=== Tests de Validación de Cantidad ==="
echo ""

# TC-004: Cantidad = 0 debe fallar
PAYLOAD_CANTIDAD_CERO=$(cat <<EOF
{
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO_ID",
      "cantidad": 0,
      "precio_unitario": 25.50,
      "opciones": []
    }
  ]
}
EOF
)

run_test "Cantidad = 0 debe retornar 400 o 422" "422" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_CANTIDAD_CERO"

# TC-005: Cantidad negativa debe fallar
PAYLOAD_CANTIDAD_NEGATIVA=$(cat <<EOF
{
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO_ID",
      "cantidad": -5,
      "precio_unitario": 25.50,
      "opciones": []
    }
  ]
}
EOF
)

run_test "Cantidad negativa debe retornar 400 o 422" "422" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_CANTIDAD_NEGATIVA"

echo ""
echo "=== Tests de Validación de Precio ==="
echo ""

# TC-006: Precio = 0 debe fallar
PAYLOAD_PRECIO_CERO=$(cat <<EOF
{
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO_ID",
      "cantidad": 1,
      "precio_unitario": 0,
      "opciones": []
    }
  ]
}
EOF
)

run_test "Precio = 0 debe retornar 400 o 422" "422" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_PRECIO_CERO"

# TC-007: Precio negativo debe fallar
PAYLOAD_PRECIO_NEGATIVO=$(cat <<EOF
{
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO_ID",
      "cantidad": 1,
      "precio_unitario": -25.50,
      "opciones": []
    }
  ]
}
EOF
)

run_test "Precio negativo debe retornar 400 o 422" "422" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_PRECIO_NEGATIVO"

echo ""
echo "=== Tests de Validación de Items Vacíos ==="
echo ""

# TC-008: Items vacío debe fallar
PAYLOAD_ITEMS_VACIO=$(cat <<EOF
{
  "id_mesa": "$MESA_ID",
  "items": []
}
EOF
)

run_test "Items vacío debe retornar 400 o 422" "422" \
    curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_ITEMS_VACIO"

echo ""
echo "=== Tests de Validación de Pedido Inexistente ==="
echo ""

# TC-009: GET pedido inexistente
run_test "GET pedido inexistente debe retornar 404" "404" \
    curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos/01INVALID000000000000000000"

# TC-010: PATCH pedido inexistente
run_test "PATCH estado de pedido inexistente debe retornar 404" "404" \
    curl -s -w "\n%{http_code}" -X PATCH "$API_URL/api/v1/pedidos/01INVALID000000000000000000/estado" \
    -H "Content-Type: application/json" \
    -d '{"estado": "CONFIRMADO"}'

# TC-011: DELETE pedido inexistente
run_test "DELETE pedido inexistente debe retornar 404" "404" \
    curl -s -w "\n%{http_code}" -X DELETE "$API_URL/api/v1/pedidos/01INVALID000000000000000000"

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
