#!/bin/bash

# Script de pruebas para Caso de Uso 4: Cambiar estado de pedido
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

# Cargar funciones comunes
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_common.sh"

echo "=========================================="
echo "  CU-04: Cambiar Estado de Pedido"
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

echo "=== Preparación: Crear pedido de prueba ==="
echo ""

# Obtener token de autenticación
get_auth_token || exit 1

# Obtener ID de usuario
echo -n "Obteniendo ID de usuario... "
USER_ID=$(curl -s "$API_URL/api/v1/auth/me" -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
echo -e "${GREEN}✓${NC} $USER_ID"

# Obtener IDs necesarios
echo -n "Obteniendo ID de mesa... "
MESA_ID=$(curl -s "$API_URL/api/v1/mesas?limit=1" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)
echo -e "${GREEN}✓${NC} $MESA_ID"

echo -n "Obteniendo ID de producto... "
PRODUCTO_RESPONSE=$(curl -s "$API_URL/api/v1/productos/cards?limit=1")
PRODUCTO_ID=$(echo "$PRODUCTO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') else '')" 2>/dev/null)
PRODUCTO_PRECIO=$(echo "$PRODUCTO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['precio_base'] if data.get('items') else 0)" 2>/dev/null)
echo -e "${GREEN}✓${NC} $PRODUCTO_ID"

# Crear pedido de prueba
echo -n "Creando pedido de prueba... "
PAYLOAD=$(cat <<EOF
{
  "id_usuario": "$USER_ID",
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO_ID",
      "cantidad": 1,
      "precio_unitario": $PRODUCTO_PRECIO,
      "opciones": []
    }
  ],
  "notas_cliente": "Test cambio de estado"
}
EOF
)

PEDIDO_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "$PAYLOAD")

PEDIDO_ID=$(echo "$PEDIDO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

if [ -n "$PEDIDO_ID" ]; then
    echo -e "${GREEN}✓${NC} Pedido ID: $PEDIDO_ID"
else
    echo -e "${RED}✗ No se pudo crear pedido${NC}"
    exit 1
fi

echo ""
echo "=== Tests de Cambio de Estado ==="
echo ""

# TC-001: Cambiar estado a CONFIRMADO
PAYLOAD_CONFIRMADO='{"estado": "confirmado"}'
ESTADO_RESPONSE=$(run_test "Cambiar estado a CONFIRMADO" "200" \
    curl -s -w "\n%{http_code}" -X PATCH "$API_URL/api/v1/pedidos/$PEDIDO_ID/estado" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_CONFIRMADO")

echo ""

# TC-002: Validar que el estado cambió a CONFIRMADO
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que estado es CONFIRMADO... "
ESTADO_ACTUAL=$(echo "$ESTADO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('estado', ''))" 2>/dev/null)

if [ "$ESTADO_ACTUAL" = "confirmado" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Estado: $ESTADO_ACTUAL)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Esperado: confirmado, Obtenido: $ESTADO_ACTUAL)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# TC-003: Validar que se actualizó fecha_confirmado
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que fecha_confirmado no es null... "
FECHA_CONFIRMADO=$(echo "$ESTADO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('fecha_confirmado', 'null'))" 2>/dev/null)

if [ "$FECHA_CONFIRMADO" != "null" ] && [ "$FECHA_CONFIRMADO" != "None" ] && [ -n "$FECHA_CONFIRMADO" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Fecha: $FECHA_CONFIRMADO)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (fecha_confirmado es null)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-004: Cambiar estado a EN_PREPARACION
PAYLOAD_EN_PREP='{"estado": "en_preparacion"}'
ESTADO_RESPONSE2=$(run_test "Cambiar estado a EN_PREPARACION" "200" \
    curl -s -w "\n%{http_code}" -X PATCH "$API_URL/api/v1/pedidos/$PEDIDO_ID/estado" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_EN_PREP")

echo ""

# TC-005: Validar que fecha_en_preparacion se actualizó
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que fecha_en_preparacion no es null... "
FECHA_EN_PREP=$(echo "$ESTADO_RESPONSE2" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('fecha_en_preparacion', 'null'))" 2>/dev/null)

if [ "$FECHA_EN_PREP" != "null" ] && [ "$FECHA_EN_PREP" != "None" ] && [ -n "$FECHA_EN_PREP" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Fecha: $FECHA_EN_PREP)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (fecha_en_preparacion es null)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-006: Cambiar estado a LISTO
PAYLOAD_LISTO='{"estado": "listo"}'
ESTADO_RESPONSE3=$(run_test "Cambiar estado a LISTO" "200" \
    curl -s -w "\n%{http_code}" -X PATCH "$API_URL/api/v1/pedidos/$PEDIDO_ID/estado" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_LISTO")

echo ""

# TC-007: Validar que fecha_listo se actualizó
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que fecha_listo no es null... "
FECHA_LISTO=$(echo "$ESTADO_RESPONSE3" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('fecha_listo', 'null'))" 2>/dev/null)

if [ "$FECHA_LISTO" != "null" ] && [ "$FECHA_LISTO" != "None" ] && [ -n "$FECHA_LISTO" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Fecha: $FECHA_LISTO)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (fecha_listo es null)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-008: Cambiar estado a ENTREGADO
PAYLOAD_ENTREGADO='{"estado": "entregado"}'
ESTADO_RESPONSE4=$(run_test "Cambiar estado a ENTREGADO" "200" \
    curl -s -w "\n%{http_code}" -X PATCH "$API_URL/api/v1/pedidos/$PEDIDO_ID/estado" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_ENTREGADO")

echo ""

# TC-009: Validar que fecha_entregado se actualizó
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que fecha_entregado no es null... "
FECHA_ENTREGADO=$(echo "$ESTADO_RESPONSE4" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('fecha_entregado', 'null'))" 2>/dev/null)

if [ "$FECHA_ENTREGADO" != "null" ] && [ "$FECHA_ENTREGADO" != "None" ] && [ -n "$FECHA_ENTREGADO" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Fecha: $FECHA_ENTREGADO)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (fecha_entregado es null)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=== Test de Estado CANCELADO ==="
echo ""

# Crear otro pedido para cancelar
echo -n "Creando segundo pedido para test de cancelación... "
PEDIDO_RESPONSE2=$(curl -s -X POST "$API_URL/api/v1/pedidos/completo" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

PEDIDO_ID2=$(echo "$PEDIDO_RESPONSE2" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
echo -e "${GREEN}✓${NC} $PEDIDO_ID2"

echo ""

# TC-010: Cambiar estado a CANCELADO
PAYLOAD_CANCELADO='{"estado": "cancelado"}'
ESTADO_RESPONSE5=$(run_test "Cambiar estado a CANCELADO" "200" \
    curl -s -w "\n%{http_code}" -X PATCH "$API_URL/api/v1/pedidos/$PEDIDO_ID2/estado" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD_CANCELADO")

echo ""

# TC-011: Validar que fecha_cancelado se actualizó
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que fecha_cancelado no es null... "
FECHA_CANCELADO=$(echo "$ESTADO_RESPONSE5" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('fecha_cancelado', 'null'))" 2>/dev/null)

if [ "$FECHA_CANCELADO" != "null" ] && [ "$FECHA_CANCELADO" != "None" ] && [ -n "$FECHA_CANCELADO" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Fecha: $FECHA_CANCELADO)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (fecha_cancelado es null)"
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
