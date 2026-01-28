from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Any, Optional, Literal, Union
import numpy as np


class ZSpec(BaseModel):
    type: str
    values: List[float]
    num: Optional[int] = None


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
    normal: Optional[List[float]] = Field(None, description="alias for orientation")
    z_range: Optional[List[float]] = None
    element_size: Optional[float] = None
    mesh: bool = True
    reference_web: Optional[str] = None
    offsets: Optional[List[List[float]]] = None
    n_elem: Optional[int] = None
    interp_method: Literal["pchip", "linear"] = "pchip"

    @model_validator(mode="after")
    def set_normal_from_orientation(self):
        if self.normal is None and self.orientation is not None:
            self.normal = self.orientation
        return self


class Structure(BaseModel):
    webs: List[Web]


class Chordwise(BaseModel):
    default: Dict[str, Any]
    panels: Optional[List[Dict[str, Any]]] = None


class Mesh2D(BaseModel):
    name: str = Field(..., description="Mesh identifier")
    type: Literal["line"]
    z: List[Dict]
    chordwise: Chordwise


class Mesh3D(BaseModel):
    name: str = Field(..., description="Mesh identifier")
    type: Literal["surface"]
    z: List[Dict]
    chordwise: Chordwise


MeshConfig = Union[Mesh2D, Mesh3D]


class Config(BaseModel):
    workdir: str
    geometry: Geometry
    airfoils: List[AirfoilItem]
    structure: Structure
    mesh: List[MeshConfig] = Field(..., description="List of mesh configurations")

    @field_validator("mesh")
    @classmethod
    def validate_unique_names(cls, v):
        names = [mesh.name for mesh in v]
        if len(names) != len(set(names)):
            raise ValueError("Mesh names must be unique")
        return v
