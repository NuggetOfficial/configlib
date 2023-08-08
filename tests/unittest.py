from configlib.configlib import UnitTests
if not UnitTests():
    raise ImportError("Package critically failed testing! Please contact me at vdwielen@strw.leidenuniv.nl or open a git issue!")
del UnitTests
