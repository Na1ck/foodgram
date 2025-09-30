import string


def id_to_base36(id):
    """
    Кодирует число в base36 строку
    """
    alphabet = string.digits + string.ascii_lowercase
    base36 = ''
    while id:
        id, i = divmod(id, 36)
        base36 = alphabet[i] + base36
    return base36 or '0'


def base36_to_id(base36):
    """
    Декодирует base36 строку в число
    """
    alphabet = string.digits + string.ascii_lowercase
    base36 = base36.lower()
    if any(c not in alphabet for c in base36):
        raise ValueError("Invalid base36 string")
    number = 0
    for char in base36:
        number = number * 36 + alphabet.index(char)
    return number
