from ...step.surface_mesh_step import B3MshSurfaceStep


def surface_process_sections(logger, mesh, z_sections, chordwise_mesh, webs_config):
    """Process sections for surface meshing."""
    logger.info("Processing sections for surface mesh")
    sections = []
    for z in z_sections:
        af = B3MshSurfaceStep.process_section_from_mesh(
            mesh, z, chordwise_mesh, webs_config, logger
        )
        sections.append(af)
    return sections
