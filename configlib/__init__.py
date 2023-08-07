from configlib import UnitTests
# do tests
if not UnitTests():
    raise Exception('package critically failed unit tests! please contact me, vdwielen@strw.leidenuniv.nl or open an issue on the github repository!')
# Test not for import
del UnitTests

# currently intented imports
from configlib import Config, FileConfig, ConfigIO