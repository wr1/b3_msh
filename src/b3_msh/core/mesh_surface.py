"""Step for processing 3D surface meshes."""

from pathlib import Path
from statesman import Statesman
from statesman.core.base import ManagedFile
from .mesh_base import MeshBaseStep
from .surface_mesh import generate_surface_mesh
import pyvista as pv
import pickle


class B3MshSurfaceStep(MeshBaseStep):
    """Statesman step for processing 3D surface meshes."""

    input_files = [
        ManagedFile(name="b3_msh/sections.pkl", non_empty=True),
    ]
    output_files = [
        "b3_msh/lm2_*_surface.vtp",
        "b3_msh/lm2_*_surface.vtm",
    ]

    def _execute(self):
        """Execute surface mesh processing."""
        self.logger.info("=== B3MshSurfaceStep: Processing surface meshes ===")
        
        self.config_model = self._load_and_validate_config()
        
        config_dir = Path(self.config_path).parent
        workdir = config_dir / self.config_model.workdir
        
        # Load sections
        sections_path = workdir / "b3_msh" / "sections.pkl"
        with open(sections_path, "rb") as f:
            sections = pickle.load(f)
        self.logger.info(f"Loaded {len(sections)} sections")
        
        # Process each surface mesh config
        for mesh_config in self.config_model.mesh.meshes:
            if mesh_config.type == "surface":
                self._process_surface_mesh(mesh_config, sections, workdir)
        
        self.logger.info("=== Surface mesh processing complete ===")

    def _process_surface_mesh(self, mesh_config, sections, workdir):
        """Process a single surface mesh config."""
        self.logger.info(f"Processing surface mesh '{mesh_config.name}'")
        self.logger.info(f"  spanwise_n_elem: {mesh_config.spanwise_n_elem}")
        self.logger.info(f"  closure: {mesh_config.closure}")
        
        z_sections = self._expand_z_locations(mesh_config.z)
        self.logger.info(f"  z-sections: {len(z_sections)} locations")
        
        # Filter sections to match z
        filtered_sections = []
        for af in sections:
            if af.current_points[0, 2] in z_sections:
                filtered_sections.append(af)
        
        # Generate surface mesh
        surface_mesh = generate_surface_mesh(
            filtered_sections,
            spanwise_n_elem=mesh_config.spanwise_n_elem,
            closure=mesh_config.closure
        )
        
        # Save outputs
        vtp_path = workdir / "b3_msh" / f"lm2_{mesh_config.name}_surface.vtp"
        vtm_path = workdir / "b3_msh" / f"lm2_{mesh_config.name}_surface.vtm"
        
        vtp_path.parent.mkdir(parents=True, exist_ok=True)
        surface_mesh.save(str(vtp_path))
        
        # VTM as MultiBlock of sections (for debugging)
        multi_block = pv.MultiBlock()
        for i, section in enumerate(filtered_sections):
            multi_block.append(section.to_pyvista(), f"z_{z_sections[i]:.1f}")
        multi_block.save(str(vtm_path))
        
        self.logger.info(f"  Saved surface mesh: {vtp_path} ({surface_mesh.n_cells:,} cells)")
        self.logger.info(f"  Saved sections: {vtm_path}")
