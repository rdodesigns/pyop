from .linop import (
      LinearOperator
    )

from .convert import(
      toScipyLinearOperator
    , toLinearOperator
    , toMatrix
    )

from .tests import adjointTest

from .utilities import ensure2dColumn, vector, vectorArray

from .block import bmat, horzcat, vertcat

from . import operators
