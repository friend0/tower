__author__ = 'empire'

import numpy as np

x = np.array([-5, 10, 4, 3456, 0.2, 0.1, 0.3, 0.4, 0.5, -10, 54, 345, 10])
mask = np.ma.masked_less_equal(x, 0.2)
print mask.filled(100000)
mask2 = np.ma.masked_values(x, -5)
print mask2
print mask2.filled(0)
