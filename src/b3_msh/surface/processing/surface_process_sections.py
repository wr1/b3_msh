from b3_msh.surface.step.b3_msh_surface_step import b3_msh_surface_step


def surface_process_sections(logger, mesh, z_sections, chordwise_mesh, webs_config):
    """Process sections for surface meshing."""
    logger.info("Processing sections for surface mesh")
    sections = []
    for z in z_sections:
        af = b3_msh_surface_step.process_section_from_mesh(
            mesh, z, chordwise_mesh, webs_config, logger
        )
        sections.append(af)
    return sections
