from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal, Union
import numpy as np


class ZSpec(BaseModel):
    type: Literal["plain", "linspace"]
    values: List[float]
    num: Optional[int] = None  # Only for linspace


class Planform(BaseModel):
    npchord: int
    dx: List[List[float]]
    dy: List[List[float]]
    z: List[List[float]]
    chord: List[List[float]]
    thickness: List[List[float]]
    twist: List[List[float]]


class Geometry(BaseModel):
    planform: Planform


class AirfoilItem(BaseModel):
    path: str
    name: str
    thickness: float


class Web(BaseModel):
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
    webs: List[Web]


class Chordwise(BaseModel):
    default: Dict[str, Any]
    panels: Optional[List[Dict[str, Any]]] = None


class Mesh2D(BaseModel):
    name: str = Field(..., description="Mesh identifier")
    type: Literal["line"]
    z: List[ZSpec]
    chordwise: Chordwise


class Mesh3D(BaseModel):
    name: str = Field(..., description="Mesh identifier")
    type: Literal["surface"]
    z: List[ZSpec]
    chordwise: Chordwise
    spanwise_n_elem: int = Field(default=20, description="Spanwise elements between sections")
    closure: Literal["open", "capped"] = Field(default="open", description="Add end caps")


MeshConfig = Union[Mesh2D, Mesh3D]


class Mesh(BaseModel):
    meshes: List[MeshConfig] = Field(..., description="List of 2D/3D mesh configurations")

    @validator("meshes")
    def validate_unique_names(cls, v):
        names = [mesh.name for mesh in v]
        if len(names) != len(set(names)):
            raise ValueError("Mesh names must be unique")
        return v


class Config(BaseModel):
    workdir: str
    geometry: Geometry
    airfoils: List[AirfoilItem]
    structure: Structure
    mesh: Union[Mesh, Dict] = Field(..., description="Mesh config (list or legacy single dict)")

    @validator("mesh", pre=True)
    def handle_legacy_mesh(cls, v):
        """Convert legacy single mesh dict to list format"""
        if isinstance(v, dict) and "z" in v and "chordwise" in v:
            # Legacy format: wrap in default line mesh
            return {
                "meshes": [
                    {
                        "name": "default",
                        "type": "line",
                        "z": [ZSpec.parse_obj({"type": "plain", "values": v["z"]}).dict()],
                        "chordwise": v["chordwise"]
                    }
                ]
            }
        return v

    @validator("mesh")
    def ensure_mesh_is_list(cls, v):
        if not isinstance(v, dict) or "meshes" not in v:
            raise ValueError("'mesh' must contain 'meshes' list or be legacy dict")
        return v


# Legacy compatibility (for existing code)
class LegacyMesh(BaseModel):
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
            "meshes": [
                {
                    "name": "2d",
                    "type": "line",
                    "z": [
                        {"type": "plain", "values": [4, 20.25, 50, 80]},
                        {"type": "linspace", "values": [3, 100], "num": 50}
                    ],
                    "chordwise": {"default": {"n_elem": 40}}
                },
                {
                    "name": "3d",
                    "type": "surface",
                    "z": [{"type": "linspace", "values": [3, 100], "num": 50}],
                    "chordwise": {"default": {"n_elem": 40}},
                    "spanwise_n_elem": 30,
                    "closure": "capped"
                }
            ]
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
