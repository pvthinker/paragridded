class HeatFlux:
    def __init__(self, reader, vinterp):
        self.vi = vinterp
        self.reader = reader
        self.rho0 = 1e3
        self.Cp = 4000.

    def compute(self, var, kz):
        self.vi.ddz(var, kz)
        coef = self.rho0*self.Cp
        AKv = var.new("AKv")
        self.reader.read(AKv)
        for tile in var:
            var._arrays[tile] *= coef*AKv[tile][kz+1]
