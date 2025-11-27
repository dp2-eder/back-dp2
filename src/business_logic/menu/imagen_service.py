"""
Servicio para gestión de imágenes de productos.

Maneja la carga, validación y almacenamiento de imágenes de productos
en el sistema de archivos.
"""

from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io
import base64
from ulid import ULID

from src.core.config import get_settings, Settings
settings: Settings = get_settings()


class ImagenService:
    """Servicio para gestión de imágenes de productos."""

    # Configuración
    STATIC_DIR = Path(settings.static_dir) / settings.images_dir
    ALLOWED_EXTENSIONS = set(settings.allowed_extensions)
    MAX_FILE_SIZE = settings.max_file_size
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
    async def save_image(cls, entity_id: str, file: UploadFile, prefix: str = "") -> str:
        """
        Guarda y optimiza una imagen de forma genérica.
        
        Parameters
        ----------
        entity_id : str
            ID de la entidad (producto, categoría, etc.)
        file : UploadFile
            Archivo de imagen a guardar
        prefix : str
            Prefijo para el nombre del archivo (ej: "categoria_")
            
        Returns
        -------
        str
            Nombre del archivo guardado
        """
        cls.ensure_directory_exists()
        cls.validate_image_file(file)
        
        contents = await file.read()
        if len(contents) > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo demasiado grande. Máximo: {cls.MAX_FILE_SIZE // (1024*1024)}MB",
            )

        filename = f"{prefix}{entity_id}.jpg"
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

    @classmethod
    async def save_producto_image(cls, producto_id: str, file: UploadFile) -> str:
        """Guarda y optimiza imagen del producto. Siempre guarda como JPG."""
        return await cls.save_image(producto_id, file, prefix="producto_")
    
    @classmethod
    async def save_categoria_image(cls, categoria_id: str, file: UploadFile) -> str:
        """Guarda y optimiza imagen de la categoría. Siempre guarda como JPG."""
        return await cls.save_image(categoria_id, file, prefix="categoria_")

    @classmethod
    async def save_screenshot_from_base64(cls, base64_string: str) -> str:
        """
        Guarda una imagen recibida en base64 como archivo JPG.
        
        Parameters
        ----------
        base64_string : str
            Cadena base64 de la imagen
            
        Returns
        -------
        str
            Nombre del archivo guardado
        """
        cls.ensure_directory_exists()
        
        try:
            # Limpiar prefijo data URI si existe (ej: data:image/png;base64,)
            if "," in base64_string:
                base64_string = base64_string.split(",")[1]
                
            # Decodificar base64
            image_data = base64.b64decode(base64_string)
            
            # Generar nombre único
            code = str(ULID())
            filename = f"domotica_{code}.jpg"
            filepath = cls.STATIC_DIR / filename
            
            # Procesar y guardar imagen
            image = Image.open(io.BytesIO(image_data))
            if image.mode != "RGB":
                if image.mode == "RGBA":
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background
                else:
                    image = image.convert("RGB")
            
            # Opcional: Redimensionar si es muy grande
            if image.size[0] > cls.MAX_DIMENSIONS[0] or image.size[1] > cls.MAX_DIMENSIONS[1]:
                image.thumbnail(cls.MAX_DIMENSIONS, Image.Resampling.LANCZOS)
                
            image.save(filepath, format="JPEG", quality=85, optimize=True)
            
            return filename
            
        except Exception as e:
            raise ValueError(f"Error al guardar screenshot: {str(e)}")
