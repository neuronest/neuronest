from typing import Optional

from fastapi.exceptions import HTTPException


def abort(code: int, detail: Optional[str] = "Whoops! Something went wrong"):
    raise HTTPException(status_code=code, detail=detail)
