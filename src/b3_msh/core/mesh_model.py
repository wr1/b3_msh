from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal, Union
import numpy as np


class ZSpec(BaseModel):
    """Specification for z values."""
    type: Literal["plain", "linspace"]
    values: List[float]
    num: Optional[int] = None  # Only for linspace


class Planform(BaseModel):
    """Planform data."""
    npchord: int
    dx: List[List[float]]
    dy: List[List[float]]
    z: List[List[float]]
    chord: List[List[float]]
    thickness: List[List[float]]
    twist: List[List[float]]


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
    origin: Optional[List[float]] = None
    orientation: Optional[List[float]] = None
    normal: Optional[List[float]] = None  # alias for orientation
    z_range: Optional[List[float]] = None
    element_size: Optional[float] = None
    mesh: bool = True
    reference_web: Optional[str] = None
    offsets: Optional[List[List[float]]] = None
    n_elem: Optional[int] = None
    interp_method: Literal["pchip", "linear"] = "pchip"

    @validator("normal", pre=True, always=True)
    def normal_or_orientation(cls, v, values):
        return v or values.get("orientation")


class Structure(BaseModel):
    """Structure configuration."""
    webs: List[Web]


class Chordwise(BaseModel):
    """Chordwise mesh configuration."""
    default: Dict[str, Any]
    panels: Optional[List[Dict[str, Any]]] = None


class Mesh(BaseModel):
    """Mesh configuration."""
    z: List[ZSpec]
    chordwise: Chordwise


class Config(BaseModel):
    """Main configuration."""
    workdir: str
    geometry: Geometry
    airfoils: List[AirfoilItem]
    structure: Structure
    mesh: Mesh


# Legacy compatibility (for existing code)
class LegacyMesh(BaseModel):
    """Legacy mesh format."""
    z: List[float]
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
                {"type": "linspace", "values": [3, 100], "num": 50}
            ],
            "chordwise": {"default": {"n_elem": 40}}
        }
    }
    config = Config(**config_data)
    print(config)

    # Test legacy
    legacy_data = {
        "workdir": "temp",
        "geometry": {"planform": {"npchord": 200}},
        "airfoils": [],
        "structure": {"webs": []},
        "mesh": {"z": [4, 20, 50], "chordwise": {"default": {"n_elem": 40}}}
    }
    legacy_config = Config(**legacy_data)
    print(legacy_config)
