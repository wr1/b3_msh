#set page(margin: 1in)
#set text(font: "New Computer Modern", size: 12pt)

= b3_msh

// author wr1 <8971152+wr1@users.noreply.github.com> 

b3_msh is a python library for handling line meshes representing airfoils with internal structure (like shear webs)

base of the airfoil is a xfoil style point list with x-y (and z) coordinates

internally this is interpolated using a spline, which has parametric coordinate t[0,1]

= functionality 

== input
- airfoils may be input as a normalized airfoil with 1 chord length, which is then scaled, rotated, and translated to the desired position
- read xfoil format airfoil files
- take in point list as a numpy
- airfoils may also be input as a full scale airfoil in 3d

== remeshing
- from original t distribution, the airfoil can be regenerated with other t distributions including local refinements or hard points
    - remeshing happens from the original spline from the input point list, to avoid drift over multiple remeshes
- remeshing can be done by specifying mesh refinement relative to current, by specifying number of points per panel, or by absolute or relative element length

== hard points
- a hard point is a point that has a node in the mesh regardless of remeshing
- a spline initially has hard points at t=0 and 1
- hard points can be given at t values (relative coordinate), a shear web is defined as two hard points connected by a straight line
- hard points can have names which steer the naming of arrays related to them 

== panels 
- a panel is a section between two hard points, with no shear webs there is only panel 0 
- if you add a shear web with hard points t=0.3 and t=0.7, then you have three panels, panel 0 from t=0 to 0.3, panel 1 from t=0.3 to 0.7, and panel 2 from t=0.7 to 1

== shear webs
- shear webs can be defined as 
    - plane (origin (x,y,z) and normal (nx,ny,nz)), intersection with airfoil gives two hard points
    - a line in 2D (intersection between airfoil and line gives two hard points)
    - relative chord position [dont implement yet]
    - absolute chord position [dont implement yet]

- shearwebs can have names, and the coordinates related to the shear web interactions then have those names, say a web is named web0, then there are abs and relative distance from web0 hard point 0 and hard point 1  along airfoil as float arrays added to the output mesh
- if hard points don't have explicit names they inherit from the shear web, default names for shear webs are web{nr} where nr is the shear web id after order of creation

= tech 
- scipy pchip for spline interpolation
- numpy, prioritize vectorized operations
- pyvista for output and meshing
- pytest and --cov 
- matplotlib for plotting
- multiprocessing on airfoil level, allowing handling of many airfoils in parallel    



