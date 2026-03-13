import os

import numpy as np
import pyvista as pv
import yaml

from b3_msh.surface.step.b3_msh_surface_step import b3_msh_surface_step
from b3_msh.utils.logger import get_logger


def load_yaml_config(config_path):
    """Load YAML configuration file."""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config


def process_sections(logger, mesh, z_values, chordwise_mesh, webs_config):
    """Process each section."""
    logger.info("Processing sections for surface mesh")
    sections = []
    for z in z_values:
        logger.info(f"Processing section at z={z}")
        af = b3_msh_surface_step.process_section_from_mesh(
            mesh, z, chordwise_mesh, webs_config, logger
        )
        sections.append(af)
    return sections


def create_and_save_surface_mesh(logger, sections, workdir):
    """Create surface mesh and save."""
    # Sort sections by z
    sections.sort(key=lambda af: af.position[2])

    all_points = []
    all_faces = []
    point_offset = 0

    section_data = []
    for i, af in enumerate(sections):
        pv_mesh = af.to_pyvista()
        points = pv_mesh.points
        lines = pv_mesh.lines.reshape(-1, 3)[:, 1:]
        panel_ids = pv_mesh.cell_data["panel_id"]
        airfoil_lines = lines[panel_ids >= 0]
        shear_web_lines = {}
        unique_panels = np.unique(panel_ids)
        for panel_id in unique_panels:
            if panel_id < 0:
                shear_web_lines[panel_id] = lines[panel_ids == panel_id]
        section_data.append(
            {
                "points": points,
                "lines": lines,
                "panel_ids": panel_ids,
                "n_points": len(points),
                "n_airfoil_lines": len(airfoil_lines),
                "shear_web_lines": shear_web_lines,
            }
        )
        shear_web_info = {k: len(v) for k, v in shear_web_lines.items()}
        logger.info(
            f"Section {i} (z={af.position[2]:.2f}): {len(points)} points, {len(airfoil_lines)} airfoil lines, shear webs: {shear_web_info}"
        )

    for i in range(len(sections) - 1):
        sec1 = section_data[i]
        sec2 = section_data[i + 1]

        # Airfoil panels
        airfoil_lines1 = sec1["lines"][sec1["panel_ids"] >= 0]
        airfoil_lines2 = sec2["lines"][sec2["panel_ids"] >= 0]

        if len(airfoil_lines1) != len(airfoil_lines2):
            logger.warning(
                f"Inconsistent airfoil elements between sections {i} ({len(airfoil_lines1)}) and {i + 1} ({len(airfoil_lines2)}), skipping"
            )
            continue

        for j in range(len(airfoil_lines1)):
            p1 = airfoil_lines1[j][0] + point_offset
            p2 = airfoil_lines1[j][1] + point_offset
            p3 = airfoil_lines2[j][1] + point_offset + sec1["n_points"]
            p4 = airfoil_lines2[j][0] + point_offset + sec1["n_points"]
            all_faces.append([4, p1, p2, p3, p4])

        # Shear webs
        unique_panels = np.unique(sec1["panel_ids"])
        for panel_id in unique_panels:
            if panel_id < 0:
                lines1 = sec1["lines"][sec1["panel_ids"] == panel_id]
                lines2 = sec2["lines"][sec2["panel_ids"] == panel_id]
                if len(lines1) != len(lines2):
                    logger.warning(
                        f"Inconsistent shear web elements for panel {panel_id} between sections {i} ({len(lines1)}) and {i + 1} ({len(lines2)}), skipping"
                    )
                    continue
                for j in range(len(lines1)):
                    p1 = lines1[j][0] + point_offset
                    p2 = lines1[j][1] + point_offset
                    p3 = lines2[j][1] + point_offset + sec1["n_points"]
                    p4 = lines2[j][0] + point_offset + sec1["n_points"]
                    all_faces.append([4, p1, p2, p3, p4])

        all_points.extend(sec1["points"])
        point_offset += sec1["n_points"]

    all_points.extend(section_data[-1]["points"])

    surface_mesh = pv.PolyData(np.array(all_points), faces=np.array(all_faces))
    output_path = os.path.join(workdir, "b3_msh", "lm2_surface_mesh.vtp")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving surface mesh to {output_path}")
    surface_mesh.save(output_path)
    logger.info(f"Saved surface mesh to {output_path}")


def main():
    logger = get_logger(__name__)
    logger.info("Starting surface meshing")

    config_path = "examples/blade_test_ribbon.yml"  # Use the ribbon config with mesh3d
    config = load_yaml_config(config_path)

    workdir = os.path.join("examples", config["workdir"])
    mesh3d_config = config["mesh3d"]
    z_specs = mesh3d_config["z"]
    z_values = []
    for z_spec in z_specs:
        if z_spec["type"] == "plain":
            z_values.extend(z_spec["values"])
        elif z_spec["type"] == "linspace":
            z_values.extend(np.linspace(z_spec["values"][0], z_spec["values"][1], z_spec["num"]))
    logger.info(f"Found z sections: {np.round(z_values, 2).tolist()}")
    chordwise_mesh = mesh3d_config["chordwise"]
    webs_config = config["structure"]["webs"]

    # Load the pre-processed mesh
    input_path = os.path.join(workdir, "b3_geo", "lm1_mesh3d.vtp")
    logger.info(f"Loading pre-processed mesh from {input_path}")
    mesh = pv.read(input_path)
    logger.info("Loaded mesh successfully")

    sections = process_sections(logger, mesh, z_values, chordwise_mesh, webs_config)
    create_and_save_surface_mesh(logger, sections, workdir)


if __name__ == "__main__":
    main()
