from ...step.blade_mesh_step import B3MshStep


def blade_process_sections(logger, mesh, z_sections, chordwise_mesh, webs_config):
    """Process sections from mesh."""
    logger.info("Processing sections")
    sections = []
    for z in z_sections:
        af = B3MshStep.process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger)
        sections.append(af)
    return sections
