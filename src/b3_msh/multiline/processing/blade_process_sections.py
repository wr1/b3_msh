from b3_msh.multiline.step.b3_msh_line_step import b3_msh_line_step


def blade_process_sections(logger, mesh, z_sections, chordwise_mesh, webs_config):
    """Process sections from mesh."""
    logger.info("Processing sections")
    sections = []
    for z in z_sections:
        af = b3_msh_line_step.process_section_from_mesh(mesh, z, chordwise_mesh, webs_config, logger)
        sections.append(af)
    return sections
