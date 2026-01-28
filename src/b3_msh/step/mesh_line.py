"""Step for processing 2D line meshes."""

import numpy as np
from pathlib import Path
from statesman import Statesman
from statesman.core.base import ManagedFile
from .mesh_base import MeshBaseStep
import pyvista as pv
import pickle


class B3MshLineStep(MeshBaseStep):
    """Statesman step for processing 2D line meshes."""

    input_files = [
        ManagedFile(name="b3_msh/sections.pkl", non_empty=True),
    ]
    output_files = [
        "b3_msh/lm2_*_line.vtp",
        "b3_msh/lm2_*_line.vtm",
    ]

    def _execute(self):
        """Execute line mesh processing."""
        self.logger.info("=== B3MshLineStep: Processing line meshes ===")
        
        self.config_model = self._load_and_validate_config()
        
        config_dir = Path(self.config_path).parent
        workdir = config_dir / self.config_model.workdir
        
        # Load sections
        sections_path = workdir / "b3_msh" / "sections.pkl"
        with open(sections_path, "rb") as f:
            sections = pickle.load(f)
        self.logger.info(f"Loaded {len(sections)} sections")
        
        # Process each line mesh config
        for mesh_config in self.config_model.mesh:
            if mesh_config.type == "line":
                self._process_line_mesh(mesh_config, sections, workdir)
        
        self.logger.info("=== Line mesh processing complete ===")

    def _process_line_mesh(self, mesh_config, sections, workdir):
        """Process a single line mesh config."""
        self.logger.info(f"Processing line mesh '{mesh_config.name}'")
        
        z_sections = self._expand_z_locations(mesh_config.z)
        self.logger.info(f"  z-sections: {len(z_sections)} locations")
        
        # Filter sections to match z
        filtered_sections = []
        for af in sections:
            if af.current_points[0, 2] in z_sections:
                filtered_sections.append(af)
        
        # Save outputs
        vtp_path = workdir / "b3_msh" / f"lm2_{mesh_config.name}_line.vtp"
        vtm_path = workdir / "b3_msh" / f"lm2_{mesh_config.name}_line.vtm"
        
        self._save_line_mesh(filtered_sections, vtp_path, format="vtp")
        self._save_line_mesh(filtered_sections, vtm_path, format="vtm")
        
        self.logger.info(f"  Saved: {vtp_path} and {vtm_path}")

    def _save_line_mesh(self, sections, output_path, format="vtp"):
        """Save line mesh in requested format."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "vtm":
            self.logger.info(f"Creating MultiBlock: {output_path}")
            multi_block = pv.MultiBlock()
            for i, af in enumerate(sections):
                mesh_out = af.to_pyvista()
                multi_block.append(mesh_out, f"z_{sections[i].current_points[0,2]:.1f}")
            multi_block.save(str(output_path))
        else:  # vtp
            self.logger.info(f"Merging line mesh: {output_path}")
            self._merge_line_meshes(sections, output_path)

    @staticmethod
    def _merge_line_meshes(sections, output_path):
        """Merge line meshes into single PolyData."""
        meshes = [af.to_pyvista() for af in sections]
        rmeshes = []
        for mesh in meshes:
            rmeshes.append(
                mesh.point_data_to_cell_data(progress_bar=False, pass_point_data=True)
            )
            for key in ["Normals", "z"]:
                if key in mesh.cell_data:
                    del mesh.cell_data[key]
        
        merged_mesh = pv.merge(rmeshes)
        
        # Fix cell_data arrays
        for field in meshes[0].point_data.keys():
            if rmeshes and field in rmeshes[0].cell_data:
                merged_values = np.concatenate(
                    [rmesh.cell_data[field] for rmesh in rmeshes]
                )
                merged_mesh.cell_data[field] = merged_values

        # Convert to PolyData
        poly = pv.PolyData()
        poly.points = merged_mesh.points
        poly.lines = merged_mesh.lines
        for key, value in merged_mesh.cell_data.items():
            poly.cell_data[key] = value
        for key, value in merged_mesh.point_data.items():
            poly.point_data[key] = value

        poly.save(str(output_path))
