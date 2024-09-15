import base64


def bytes_to_string(element: bytes, encoding: str = "utf-8") -> str:
    return base64.b64encode(element).decode(encoding)


def string_to_bytes(element: str, encoding: str = "utf-8") -> bytes:
    return base64.b64decode(element.encode(encoding))
