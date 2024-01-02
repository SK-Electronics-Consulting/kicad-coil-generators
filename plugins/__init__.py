from .coil_generator import CoilGeneratorID2L
CoilGeneratorID2L().register()

from .coil_generator import CoilGenerator1L1T
CoilGenerator1L1T().register()

from .flux_neutral_coil_generator import FluxNeutralCoilGen
FluxNeutralCoilGen().register()
