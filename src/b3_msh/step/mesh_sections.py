"""Step for extracting airfoil sections from mesh."""

import numpy as np
from pathlib import Path
from statesman import Statesman
from statesman.core.base import ManagedFile
from .mesh_base import MeshBaseStep


class B3MshSectionStep(MeshBaseStep):
    """Statesman step for extracting airfoil sections from pre-processed mesh."""

    output_files = [
        "b3_msh/sections.pkl",  # Pickle file with sections list
    ]

    def _execute(self):
        """Execute section extraction."""
        self.logger.info("=== B3MshSectionStep: Extracting airfoil sections ===")
        
        self.config_model = self._load_and_validate_config()
        
        config_dir = Path(self.config_path).parent
        workdir = config_dir / self.config_model.workdir
        
        input_path = workdir / "b3_geo" / "lm1_mesh.vtp"
        mesh = self._load_mesh(input_path)
        
        # Get all z sections
        z_sections = np.unique(mesh.points[:, 2])
        z_sections = np.sort(z_sections)
        self.logger.info(f"Found {len(z_sections)} z sections")
        
        # Process all sections
        sections = []
        chordwise_mesh = self.config_model.mesh[0].chordwise.model_dump()  # Assume first mesh for now
        webs_config = [web.model_dump() for web in self.config_model.structure.webs]
        
        for z in z_sections:
            af = self.process_section_from_mesh(
                mesh, z, chordwise_mesh, webs_config, self.logger
            )
            sections.append(af)
        
        # Save sections to pickle
        import pickle
        output_path = workdir / "b3_msh" / "sections.pkl"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(sections, f)
        
        self.logger.info(f"Saved {len(sections)} sections to {output_path}")
        self.logger.info("=== Section extraction complete ===")
