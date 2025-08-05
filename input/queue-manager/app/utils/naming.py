import re

def sanitize_name(name: str) -> str:
    """
    Преобразует имя в допустимый формат для Kubernetes ресурсов (DNS-1123):
    - строчные буквы, цифры, дефисы
    - начинается и заканчивается на букву или цифру
    """
    name = name.lower()
    name = re.sub(r"[^a-z0-9\-]", "-", name)
    name = re.sub(r"^-+|-+$", "", name)
    name = re.sub(r"-+", "-", name)
    return name[:63]

