## @file spec_field.py
#  @brief Setup the SPEC magnetic field system for ODE solver
#  @author Zhisong Qu (zhisong.qu@anu.edu.au)
#
from .spec_problem import SPECProblem
import numpy as np

## Class that used to setup the SPEC bfield problem for interfacing Fortran, used in ODE solver.
# See \ref specbfield for more details.
#
# The SPECBfield system of ODEs is given by
# \f[ \frac{ds}{d\zeta} = \frac{B^{s}}{B^{\zeta}}  \f]
# \f[ \frac{d\theta}{d\zeta} = \frac{B^{\theta}}{B^{\zeta}}  \f]
class SPECBfield(SPECProblem):

    ## the problem size, 2 for 1.5D/2D Hamiltonian system

    def __init__(self, spec_data, lvol):
        """! Set up the equilibrium for use of the fortran module
        @param spec_data the SPEC data generated by py_spec.SPECout
        @param lvol which volume we are interested in, from 1 to spec_data.input.Mvol
        Only support SPEC version >=3.0
        """
        super().__init__(spec_data, lvol)
        self.problem_size = 2
        if self.Igeometry == 1:
            self.poincare_plot_type = "yx"
            self.poincare_plot_xlabel = r"$\theta$"
            self.poincare_plot_ylabel = r"R"
        elif self.Igeometry == 2:
            self.poincare_plot_type = "RZ"
            self.poincare_plot_xlabel = "X(m)"
            self.poincare_plot_ylabel = "Y(m)"
        elif self.Igeometry == 3:
            self.poincare_plot_type = "RZ"
            self.poincare_plot_xlabel = "R(m)"
            self.poincare_plot_ylabel = "Z(m)"
        else:
            raise ValueError("Unknown Igeometry!")

    def f(self, zeta, st, arg1=None):
        """! Python wrapper for magnetic field ODE RHS
        @param zeta the zeta coordinate
        @param st   array size 2, the (s, theta) coordinate
        @param arg1 parameter for the ODE, not used here
        @returns    array size 2, the RHS of the ODE
        """
        return self.fortran_module.specbfield.get_bfield(zeta, st)

    def f_tangent(self, zeta, st, arg1=None):
        """! Python wrapper for magnetic field ODE RHS, with RHS
        @param zeta the zeta coordinate
        @param st   array size 6, the (s, theta, ds1, dtheta1, ds2, dtheta2) coordinate
        @param arg1 parameter for the ODE, not used here
        """
        return self.fortran_module.specbfield.get_bfield_tangent(zeta, st)

    def convert_coords(self, stz):
        """! Python wrapper for getting the xyz coordinates from stz
        @param stz  the stz coordinate
        @returns the xyz coordinates
        """
        xyz = self.fortran_module.speccoords.get_xyz(stz)

        # depending on the geometry, return RZ or yx
        if self.Igeometry == 1:
            # for a slab, return x=R, y=theta, z=zeta
            return np.array(
                [
                    xyz[0],
                    np.mod(stz[1], 2 * np.pi) * self.rpol,
                    np.mod(stz[2], 2 * np.pi) * self.rtor,
                ],
                dtype=np.float64,
            )
        if self.Igeometry == 2:
            # for cylinderical geometry, return x=r*cos theta, y=zeta*rtor, z=sin theta
            return np.array(
                [xyz[0] * np.cos(stz[1]), stz[2] * self.rtor, xyz[0] * np.sin(stz[1])],
                dtype=np.float64,
            )
        if self.Igeometry == 3:
            # for toroidal geometry, return x=R, y=zeta, z=Z
            return xyz
