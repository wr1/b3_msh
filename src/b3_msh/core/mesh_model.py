from pydantic import BaseModel
from typing import List, Dict, Any, Optional


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
    type: str
    origin: Optional[List[float]] = None
    orientation: Optional[List[float]] = None
    z_range: Optional[List[float]] = None
    element_size: Optional[float] = None
    mesh: bool
    reference_web: Optional[str] = None
    offsets: Optional[List[List[float]]] = None


class Structure(BaseModel):
    webs: List[Web]


class Chordwise(BaseModel):
    default: Dict[str, Any]
    panels: List[Dict[str, Any]]


class Mesh(BaseModel):
    z: List[float]
    chordwise: Chordwise


class Config(BaseModel):
    workdir: str
    geometry: Geometry
    airfoils: List[AirfoilItem]
    structure: Structure
    mesh: Mesh
