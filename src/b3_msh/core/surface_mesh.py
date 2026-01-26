"""3D surface mesh generation from airfoil sections."""

import numpy as np
import pyvista as pv
from typing import List
from .airfoil import Airfoil


def connect_sections(
    section1: Airfoil, section2: Airfoil, n_spanwise: int = 20
) -> pv.UnstructuredGrid:
    """Connect two consecutive airfoil sections with quad elements."""
    
    points1 = section1.current_points
    points2 = section2.current_points
    t1 = section1.current_t
    t2 = section2.current_t
    
    # Find best point correspondence using t-parameter matching
    all_points = []
    all_cells = []
    cell_data = []
    
    # For each point in section1, find closest t-match in section2
    for i, t1_i in enumerate(t1):
        # Find closest t in section2
        t_diff = np.abs(t2 - t1_i)
        j_closest = np.argmin(t_diff)
        
        p1 = points1[i]
        p2 = points2[j_closest]
        
        # Create spanwise subdivision
        span_points = np.linspace(p1, p2, n_spanwise + 1)
        all_points.extend(span_points)
        
        # Create quad cells (n_spanwise quads per chordwise location)
        for k in range(n_spanwise):
            # Quad: bottom-left, bottom-right, top-right, top-left
            idx_bl = len(all_points) - (n_spanwise + 1) + k
            idx_br = idx_bl + 1
            idx_tr = len(all_points) - 1 - (n_spanwise - k)
            idx_tl = idx_tr - 1
            
            all_cells.extend([4, idx_bl, idx_br, idx_tr, idx_tl])
            cell_data.extend([
                section1.rel_span,  # rel_span
                (section1.current_points[0, 2] + section2.current_points[0, 2]) / 2,  # z_mid
                t1_i,  # t_chord
                float(k) / n_spanwise  # w_span
            ])
    
    all_points = np.array(all_points)
    
    # Create unstructured grid
    ugrid = pv.UnstructuredGrid(
        all_points, np.array(all_cells)
    )
    
    # Add cell data
    ugrid.cell_data["rel_span"] = np.full(len(cell_data)//4, section1.rel_span)
    ugrid.cell_data["z"] = np.full(len(cell_data)//4, cell_data[1::4])
    ugrid.cell_data["t_chord"] = np.full(len(cell_data)//4, cell_data[0::4])
    ugrid.cell_data["w_span"] = np.full(len(cell_data)//4, cell_data[3::4])
    
    # Copy panel_id from sections (approximate)
    panel_ids1 = section1.to_pyvista().cell_data["panel_id"]
    panel_ids2 = section2.to_pyvista().cell_data["panel_id"]
    panel_ids = (panel_ids1[:-1] + panel_ids2[:-1]) / 2  # Average
    ugrid.cell_data["panel_id"] = panel_ids[:len(cell_data)//4]
    
    return ugrid


def merge_surfaces(surface_sections: List[pv.UnstructuredGrid]) -> pv.PolyData:
    """Merge multiple surface sections into single mesh."""
    if not surface_sections:
        raise ValueError("No surface sections to merge")
    
    merged = surface_sections[0]
    for section in surface_sections[1:]:
        merged += section
    
    return merged


def add_caps(surface_mesh: pv.UnstructuredGrid, cap_type: str = "both") -> pv.UnstructuredGrid:
    """Add end caps to surface mesh."""
    # Extract first/last spanwise rings
    n_points_per_ring = surface_mesh.n_cells // 20  # Approximate
    
    if cap_type in ["root", "both"]:
        # Root cap (first ring)
        root_points = surface_mesh.points[:n_points_per_ring]
        root_triangles = _triangulate_ring(root_points)
        surface_mesh += pv.UnstructuredGrid(root_triangles)
    
    if cap_type in ["tip", "both"]:
        # Tip cap (last ring)
        tip_start = -n_points_per_ring
        tip_points = surface_mesh.points[tip_start:]
        tip_triangles = _triangulate_ring(tip_points)
        surface_mesh += pv.UnstructuredGrid(tip_triangles)
    
    return surface_mesh


def _triangulate_ring(points: np.ndarray) -> tuple:
    """Convert closed ring to triangle fan."""
    n = len(points)
    cells = []
    for i in range(n-2):
        cells.extend([3, 0, i+1, i+2])
    return points, np.array(cells)


def generate_surface_mesh(
    sections: List[Airfoil],
    spanwise_n_elem: int = 20,
    closure: str = "open"
) -> pv.PolyData:
    """Generate complete surface mesh from airfoil sections."""
    
    if len(sections) < 2:
        raise ValueError("Need at least 2 sections for surface mesh")
    
    # Sort sections by z
    sections.sort(key=lambda s: s.current_points[0, 2])
    
    surface_sections = []
    for i in range(len(sections) - 1):
        section_mesh = connect_sections(
            sections[i], sections[i+1],
            n_spanwise=spanwise_n_elem
        )
        surface_sections.append(section_mesh)
    
    # Merge all surface sections
    merged_surface = merge_surfaces(surface_sections)
    
    # Add caps if requested
    if closure != "open":
        merged_surface = add_caps(merged_surface, closure)
    
    return merged_surface
