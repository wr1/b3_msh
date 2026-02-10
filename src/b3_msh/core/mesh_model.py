from typing import Any, Literal, Optional

from pydantic import BaseModel, field_validator

from .mesh3d_model import Mesh3D


class ZSpec(BaseModel):
    """Specification for z values."""

    type: Literal["plain", "linspace"]
    values: list[float]
    num: Optional[int] = None  # Only for linspace


class Planform(BaseModel):
    """Planform data."""

    npchord: int
    dx: list[list[float]]
    dy: list[list[float]]
    z: list[list[float]]
    chord: list[list[float]]
    thickness: list[list[float]]
    twist: list[list[float]]


class Geometry(BaseModel):
    """Geometry configuration."""

    planform: Planform


class AirfoilItem(BaseModel):
    """Airfoil item."""

    path: str
    name: str
    thickness: float


class Web(BaseModel):
    """Shear web configuration."""

    name: str
    type: Literal["plane", "line", "ribbon", "trailing_edge"]
    origin: Optional[list[float]] = None
    orientation: Optional[list[float]] = None
    normal: Optional[list[float]] = None  # alias for orientation
    z_range: Optional[list[float]] = None
    element_size: Optional[float] = None
    mesh: bool = True
    reference_web: Optional[str] = None
    offsets: Optional[list[list[float]]] = None
    n_elem: Optional[int] = None
    interp_method: Literal["pchip", "linear"] = "pchip"

    @field_validator("normal", mode="before")
    @classmethod
    def normal_or_orientation(cls, v, info):
        return v or info.data.get("orientation")


class Structure(BaseModel):
    """Structure configuration."""

    webs: list[Web]


class Chordwise(BaseModel):
    """Chordwise mesh configuration."""

    default: dict[str, Any]
    panels: Optional[list[dict[str, Any]]] = None


class Mesh(BaseModel):
    """Mesh configuration."""

    z: list[ZSpec]
    chordwise: Chordwise


class Config(BaseModel):
    """Main configuration."""

    workdir: str
    geometry: Geometry
    airfoils: list[AirfoilItem]
    structure: Structure
    mesh: Mesh
    mesh3d: Optional[Mesh3D] = None


# Legacy compatibility (for existing code)
class LegacyMesh(BaseModel):
    """Legacy mesh format."""

    z: list[float]
    chordwise: Chordwise


if __name__ == "__main__":
    # Test parsing
    config_data = {
        "workdir": "temp_blade",
        "geometry": {"planform": {"npchord": 200}},
        "airfoils": [],
        "structure": {"webs": []},
        "mesh": {
            "z": [
                {"type": "plain", "values": [4, 20.25, 50, 80]},
                {"type": "linspace", "values": [3, 100], "num": 50},
            ],
            "chordwise": {"default": {"n_elem": 40}},
        },
    }
    config = Config(**config_data)

    # Test legacy
    legacy_data = {
        "workdir": "temp",
        "geometry": {"planform": {"npchord": 200}},
        "airfoils": [],
        "structure": {"webs": []},
        "mesh": {"z": [4, 20, 50], "chordwise": {"default": {"n_elem": 40}}},
    }
    legacy_config = Config(**legacy_data)
