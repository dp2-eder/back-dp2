"""
Servicio para gestión de imágenes de productos.

Maneja la carga, validación y almacenamiento de imágenes de productos
en el sistema de archivos.
"""

from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io


class ProductoImagenService:
    """Servicio para gestión de imágenes de productos."""

    # Configuración
    STATIC_DIR = Path("app/static/images")
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_DIMENSIONS = (2048, 2048)

    @classmethod
    def ensure_directory_exists(cls) -> None:
        """Crea el directorio de imágenes si no existe."""
        cls.STATIC_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_image_file(cls, file: UploadFile) -> None:
        """Valida extensión del archivo."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no tiene nombre",
            )

        extension = file.filename.split(".")[-1].lower()
        if extension not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato no permitido: {', '.join(cls.ALLOWED_EXTENSIONS)}",
            )

    @classmethod
    async def save_producto_image(cls, producto_id: str, file: UploadFile) -> str:
        """Guarda y optimiza imagen del producto. Siempre guarda como JPG."""
        cls.ensure_directory_exists()
        cls.validate_image_file(file)
        
        contents = await file.read()
        if len(contents) > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo demasiado grande. Máximo: {cls.MAX_FILE_SIZE // (1024*1024)}MB",
            )

        filename = f"{producto_id}.jpg"
        filepath = cls.STATIC_DIR / filename

        try:
            image = Image.open(io.BytesIO(contents))
            if image.mode != "RGB":
                if image.mode == "RGBA":
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background
                else:
                    image = image.convert("RGB")

            if image.size[0] > cls.MAX_DIMENSIONS[0] or image.size[1] > cls.MAX_DIMENSIONS[1]:
                image.thumbnail(cls.MAX_DIMENSIONS, Image.Resampling.LANCZOS)

            image.save(filepath, format="JPEG", quality=85, optimize=True)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al procesar imagen: {str(e)}",
            )

        return filename
