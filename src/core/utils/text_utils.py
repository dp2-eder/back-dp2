"""
Utilidades para formateo y normalización de texto.
"""

def normalize_to_title_case(text: str) -> str:
    """
    Normaliza un texto a formato Title Case (Primera Letra De Cada Palabra En Mayúscula).
    
    Convierte cualquier formato de texto (MAYÚSCULAS, minúsculas, MiXtO) a un formato
    consistente donde la primera letra de cada palabra está en mayúscula y el resto 
    en minúscula.
    
    Parameters
    ----------
    text : str
        El texto a normalizar.
        
    Returns
    -------
    str
        El texto normalizado en formato Title Case.
        
    Examples
    --------
    >>> normalize_to_title_case("BEBIDAS CALIENTES")
    'Bebidas Calientes'
    >>> normalize_to_title_case("postres especiales")
    'Postres Especiales'
    >>> normalize_to_title_case("PlAtOs PrInCiPaLeS")
    'Platos Principales'
    """
    if not text or not isinstance(text, str):
        return text
    
    return text.strip().title()


def normalize_to_smart_title_case(text: str) -> str:
    """
    Normaliza un texto a formato Title Case inteligente, manteniendo preposiciones 
    y artículos en minúscula para un formato más elegante.
    
    Las preposiciones y artículos comunes se mantienen en minúscula, excepto si 
    aparecen al inicio del texto.
    
    Parameters
    ----------
    text : str
        El texto a normalizar.
        
    Returns
    -------
    str
        El texto normalizado en formato Smart Title Case.
        
    Examples
    --------
    >>> normalize_to_smart_title_case("aji de gallina")
    'Ají de Gallina'
    >>> normalize_to_smart_title_case("SUSPIRO A LA LIMEÑA")
    'Suspiro a la Limeña'
    >>> normalize_to_smart_title_case("ARROZ CON POLLO")
    'Arroz con Pollo'
    """
    if not text or not isinstance(text, str):
        return text
    
    # Lista de preposiciones y artículos comunes en español que deben ir en minúscula
    lowercase_words = {
        'a', 'al', 'con', 'de', 'del', 'en', 'la', 'las', 'el', 'los', 
        'y', 'e', 'o', 'u', 'por', 'para', 'sin', 'sobre', 'bajo',
        'ante', 'tras', 'desde', 'hasta'
    }
    
    # Limpiar y separar en palabras
    words = text.strip().split()
    if not words:
        return text
    
    result = []
    for i, word in enumerate(words):
        # La primera palabra siempre se capitaliza
        if i == 0:
            result.append(word.capitalize())
        else:
            # Si la palabra (sin acentos para comparar) está en la lista, va en minúscula
            word_lower = word.lower()
            if word_lower in lowercase_words:
                result.append(word_lower)
            else:
                result.append(word.capitalize())
    
    return ' '.join(result)


def normalize_category_name(category_name: str) -> str:
    """
    Normaliza específicamente el nombre de una categoría.
    
    Aplica la normalización de Smart Title Case manteniendo preposiciones 
    y artículos en minúscula para un formato más elegante.
    
    Parameters
    ----------
    category_name : str
        El nombre de la categoría a normalizar.
        
    Returns
    -------
    str
        El nombre de la categoría normalizado.
        
    Examples
    --------
    >>> normalize_category_name("bebidas con alcohol")
    'Bebidas con Alcohol'
    >>> normalize_category_name("POSTRES DE LA CASA")
    'Postres de la Casa'
    """
    if not category_name or not isinstance(category_name, str):
        return category_name
    
    return normalize_to_smart_title_case(category_name)


def normalize_product_name(product_name: str) -> str:
    """
    Normaliza específicamente el nombre de un producto/plato.
    
    Aplica la normalización de Smart Title Case manteniendo preposiciones 
    y artículos en minúscula para un formato más elegante y profesional.
    
    Parameters
    ----------
    product_name : str
        El nombre del producto a normalizar.
        
    Returns
    -------
    str
        El nombre del producto normalizado.
        
    Examples
    --------
    >>> normalize_product_name("aji de gallina")
    'Ají de Gallina'
    >>> normalize_product_name("SUSPIRO A LA LIMEÑA")
    'Suspiro a la Limeña'
    >>> normalize_product_name("ArRoZ cOn MaRiScOs")
    'Arroz con Mariscos'
    >>> normalize_product_name("CEVICHE MIXTO")
    'Ceviche Mixto'
    """
    if not product_name or not isinstance(product_name, str):
        return product_name
    
    return normalize_to_smart_title_case(product_name)
