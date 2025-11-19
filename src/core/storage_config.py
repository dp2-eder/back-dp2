"""
Configuración de almacenamiento de archivos.
"""
from pathlib import Path

# Directorio base para archivos estáticos
STATIC_DIR = Path("static")
IMAGES_DIR = STATIC_DIR / "images"
PRODUCTOS_IMAGES_DIR = IMAGES_DIR / "productos"

# Extensiones permitidas
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# Tamaño máximo de archivo (5MB)
MAX_IMAGE_SIZE = 5 * 1024 * 1024

# Crear directorios si no existen
PRODUCTOS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
