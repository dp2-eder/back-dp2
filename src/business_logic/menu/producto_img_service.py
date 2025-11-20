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
    MAX_DIMENSIONS = (2048, 2048)  # Ancho x Alto máximo

    @classmethod
    def ensure_directory_exists(cls) -> None:
        """Crea el directorio de imágenes si no existe."""
        cls.STATIC_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_image_file(cls, file: UploadFile) -> None:
        """
        Valida el archivo de imagen subido.

        Parameters
        ----------
        file : UploadFile
            Archivo subido a validar.

        Raises
        ------
        HTTPException
            Si el archivo no cumple con los requisitos.
        """
        # Validar extensión
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no tiene nombre"
            )

        extension = file.filename.split(".")[-1].lower()
        if extension not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato no permitido. Use: {', '.join(cls.ALLOWED_EXTENSIONS)}"
            )

        # Validar content type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser una imagen"
            )

    @classmethod
    async def save_producto_image(
        cls,
        producto_id: str,
        file: UploadFile,
        optimize: bool = True
    ) -> str:
        """
        Guarda la imagen de un producto.

        Parameters
        ----------
        producto_id : str
            ID del producto (ULID).
        file : UploadFile
            Archivo de imagen subido.
        optimize : bool, optional
            Si True, optimiza la imagen (redimensiona y comprime), por defecto True.

        Returns
        -------
        str
            Ruta relativa de la imagen guardada.

        Raises
        ------
        HTTPException
            Si hay errores en la validación o guardado.
        """
        # Asegurar que el directorio existe
        cls.ensure_directory_exists()

        # Validar archivo
        cls.validate_image_file(file)

        # Leer contenido del archivo
        contents = await file.read()

        # Validar tamaño
        if len(contents) > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo demasiado grande. Máximo: {cls.MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Obtener extensión original (ya validado en validate_image_file)
        assert file.filename is not None  # Para el type checker
        extension = file.filename.split(".")[-1].lower()

        # Nombre del archivo: {producto_id}.{extension}
        filename = f"{producto_id}.{extension}"
        filepath = cls.STATIC_DIR / filename

        try:
            if optimize:
                # Optimizar imagen con PIL
                image = Image.open(io.BytesIO(contents))

                # Convertir RGBA a RGB si es necesario
                if image.mode == "RGBA":
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background
                elif image.mode != "RGB":
                    image = image.convert("RGB")

                # Redimensionar si excede dimensiones máximas
                if image.size[0] > cls.MAX_DIMENSIONS[0] or image.size[1] > cls.MAX_DIMENSIONS[1]:
                    image.thumbnail(cls.MAX_DIMENSIONS, Image.Resampling.LANCZOS)

                # Guardar optimizada
                image.save(filepath, format="JPEG", quality=85, optimize=True)
                filename = f"{producto_id}.jpg"  # Siempre guardamos como jpg optimizado
                filepath = cls.STATIC_DIR / filename

            else:
                # Guardar archivo original sin optimizar
                with open(filepath, "wb") as f:
                    f.write(contents)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al guardar la imagen: {str(e)}"
            )

        # Retornar ruta relativa
        return f"/static/images/{filename}"

    @classmethod
    def delete_producto_image(cls, producto_id: str) -> bool:
        """
        Elimina todas las imágenes asociadas a un producto.

        Parameters
        ----------
        producto_id : str
            ID del producto.

        Returns
        -------
        bool
            True si se eliminó alguna imagen, False si no había imágenes.
        """
        deleted = False

        # Buscar archivos que empiecen con el producto_id
        for ext in cls.ALLOWED_EXTENSIONS:
            filepath = cls.STATIC_DIR / f"{producto_id}.{ext}"
            if filepath.exists():
                filepath.unlink()
                deleted = True

        return deleted

    @classmethod
    def get_producto_image_path(cls, producto_id: str) -> Optional[str]:
        """
        Obtiene la ruta de la imagen de un producto si existe.

        Parameters
        ----------
        producto_id : str
            ID del producto.

        Returns
        -------
        Optional[str]
            Ruta relativa de la imagen o None si no existe.
        """
        # Buscar archivo con cualquier extensión permitida
        for ext in cls.ALLOWED_EXTENSIONS:
            filepath = cls.STATIC_DIR / f"{producto_id}.{ext}"
            if filepath.exists():
                return f"/static/images/{producto_id}.{ext}"

        return None
