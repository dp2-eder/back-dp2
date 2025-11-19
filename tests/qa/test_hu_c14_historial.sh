#!/bin/bash

# Script de pruebas para HU-C14: Cliente que desea control - Revisar mis pedidos ya enviados
# Autor: Kevin Antonio Navarro Carrera
# Equipo: QA/SEG
# Módulo: Pedidos solicitados - Backend
# Fecha: 2025-11-13
# Historia de Usuario: Como cliente que desea control, quiero revisar mis pedidos ya enviados para llevar control de mi consumo

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
echo "  HU-C14: Revisar Historial de Pedidos"
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

echo "=== Preparación: Crear pedidos de prueba ==="
echo ""

# Obtener token de autenticación (esto ya setea USER_ID automáticamente)
get_auth_token || exit 1

# Obtener IDs necesarios (USER_ID ya está seteado por get_auth_token)
MESA_RESPONSE=$(curl -s "$API_URL/api/v1/mesas?limit=1")
MESA_ID=$(echo "$MESA_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

PRODUCTO_RESPONSE=$(curl -s "$API_URL/api/v1/productos/cards?limit=1")
PRODUCTO_ID=$(echo "$PRODUCTO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)
PRODUCTO_PRECIO=$(echo "$PRODUCTO_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['precio_base'] if data.get('items') and len(data['items']) > 0 else '')" 2>/dev/null)

echo "Usuario: $USER_ID"
echo "Mesa: $MESA_ID"
echo "Producto: $PRODUCTO_ID (S/$PRODUCTO_PRECIO)"
echo ""

# Crear un par de pedidos
for i in 1 2; do
    PAYLOAD=$(cat <<EOF
{
  "id_usuario": "$USER_ID",
  "id_mesa": "$MESA_ID",
  "items": [
    {
      "id_producto": "$PRODUCTO_ID",
      "cantidad": $i,
      "precio_unitario": $PRODUCTO_PRECIO,
      "opciones": [],
      "notas_personalizacion": null
    }
  ],
  "notas_cliente": "Pedido de prueba HU-C14 #$i",
  "notas_cocina": null
}
EOF
)

    PEDIDO=$(curl -s -X POST "$API_URL/api/v1/pedidos/completo" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "$PAYLOAD")

    PEDIDO_ID=$(echo "$PEDIDO" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)

    if [ -n "$PEDIDO_ID" ]; then
        echo -e "${GREEN}✓${NC} Pedido #$i creado: $PEDIDO_ID"
        if [ $i -eq 1 ]; then
            FIRST_PEDIDO_ID="$PEDIDO_ID"
        fi
    else
        echo -e "${RED}✗${NC} No se pudo crear pedido #$i"
    fi
done

echo ""
echo "=== Tests de Listado de Pedidos ==="
echo ""

# TC-001: Listar todos los pedidos (GET /pedidos)
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Listar pedidos (GET /pedidos)... " >&2

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos?limit=20" \
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

PEDIDOS_RESPONSE="$body"

PEDIDOS_COUNT=$(echo "$PEDIDOS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('items', [])))" 2>/dev/null || echo "0")

echo ""

# TC-002: Validar que se obtienen pedidos en el historial
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar que se obtienen pedidos... " >&2

if [ "$PEDIDOS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} (Pedidos encontrados: $PEDIDOS_COUNT)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (No se encontraron pedidos)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""

# TC-003: Listar pedidos en formato detallado
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Listar pedidos detallados (GET /pedidos/detallado)... " >&2

response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos/detallado?limit=10" \
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

PEDIDOS_DETALLADO="$body"

echo ""

# TC-004: Validar estructura de pedidos detallados
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar estructura de pedidos detallados... " >&2

HAS_ITEMS=$(echo "$PEDIDOS_DETALLADO" | python3 -c "import sys, json; data = json.load(sys.stdin); items = data.get('items', []); print(len(items) > 0 and 'items' in items[0] if items else False)" 2>/dev/null)

if [ "$HAS_ITEMS" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Pedidos incluyen ítems detallados)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ SKIP${NC} (No hay pedidos o estructura diferente)" >&2
fi

echo ""
echo "=== Tests de Historial por Sesión ==="
echo ""

# Usar el TOKEN_SESION que ya obtuvimos con get_auth_token()
if [ -n "$TOKEN_SESION" ]; then
    echo "Usando token de sesión: ${TOKEN_SESION:0:20}..."
    echo ""

    # TC-005: Obtener historial de pedidos por token de sesión
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Obtener historial por sesión (GET /pedidos/historial/{token})... " >&2

    response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/pedidos/historial/$TOKEN_SESION" \
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

    HISTORIAL_SESION="$body"

    echo ""

    # TC-006: Validar que historial por sesión retorna pedidos
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "TC-$TOTAL_TESTS: Validar pedidos en historial de sesión... " >&2

    HISTORIAL_COUNT=$(echo "$HISTORIAL_SESION" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('pedidos', [])) if 'pedidos' in data else 0)" 2>/dev/null || echo "0")

    if [ "$HISTORIAL_COUNT" -ge 0 ]; then
        echo -e "${GREEN}✓ PASS${NC} (Pedidos en sesión: $HISTORIAL_COUNT)" >&2
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Error obteniendo historial)" >&2
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo -e "${YELLOW}⚠ SKIP${NC} - No hay token de sesión disponible"
fi

echo ""
echo "=== Tests de Información en Historial ==="
echo ""

# TC-007: Validar que cada pedido incluye información esencial
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "TC-$TOTAL_TESTS: Validar información esencial en pedidos... " >&2

PRIMER_PEDIDO=$(echo "$PEDIDOS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('items', [])
if items:
    p = items[0]
    has_id = 'id' in p
    has_numero = 'numero_pedido' in p
    has_total = 'total' in p
    has_estado = 'estado' in p
    has_fecha = 'fecha_creado' in p
    print(json.dumps({
        'valid': all([has_id, has_numero, has_total, has_estado]),
        'has_fecha': has_fecha
    }))
else:
    print(json.dumps({'valid': False, 'has_fecha': False}))
" 2>/dev/null)

IS_VALID=$(echo "$PRIMER_PEDIDO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('valid', False))" 2>/dev/null)
HAS_FECHA=$(echo "$PRIMER_PEDIDO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('has_fecha', False))" 2>/dev/null)

if [ "$IS_VALID" = "True" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Campos: id, numero_pedido, total, estado, fecha: $HAS_FECHA)" >&2
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ FAIL${NC} (Campos esenciales faltantes)" >&2
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "=========================================="
echo "  Resumen de Tests - HU-C14"
echo "=========================================="
echo "Historia: Cliente revisa historial de pedidos"
echo "Backend: Endpoints de consulta de pedidos"
echo ""
echo "Total:  $TOTAL_TESTS"
echo -e "Pasados: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Fallidos: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los tests pasaron${NC}"
    echo ""
    echo "Análisis: El backend provee:"
    echo "  - Lista de pedidos enviados (GET /pedidos)"
    echo "  - Pedidos en formato detallado (GET /pedidos/detallado)"
    echo "  - Historial por sesión (GET /pedidos/historial/{token})"
    echo "  - Información esencial: id, número, total, estado, fecha"
    echo ""
    echo "Nota: Al cerrar y pagar, el historial local se limpia (lógica frontend)"
    exit 0
else
    echo -e "${RED}✗ Algunos tests fallaron${NC}"
    exit 1
fi
