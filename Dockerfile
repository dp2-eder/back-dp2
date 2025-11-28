FROM python:3.12-slim

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear usuario sin privilegios
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Exponer puerto
EXPOSE 8000

# Verificación de salud
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Ejecutar la aplicación
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]