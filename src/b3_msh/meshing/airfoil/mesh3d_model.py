from typing import Any, Literal, Optional

from pydantic import BaseModel


class ZSpec3D(BaseModel):
    """Specification for z values in 3D mesh."""

    type: Literal["plain", "linspace"]
    values: list[float]
    num: Optional[int] = None


class Chordwise3D(BaseModel):
    """Chordwise mesh configuration for 3D."""

    default: dict[str, Any]
    panels: Optional[list[dict[str, Any]]] = None


class Mesh3D(BaseModel):
    """3D mesh configuration for surface meshing."""

    z: list[ZSpec3D]
    chordwise: Chordwise3D
