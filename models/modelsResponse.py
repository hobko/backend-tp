from typing import List

from pydantic import BaseModel


class HelloResponse(BaseModel):
    message: str = "System is up"


class GraphResponse(BaseModel):
    message: str = "OK"

