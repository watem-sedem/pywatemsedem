import numpy as np
import pytest

from pywatemsedem.cfactor import reduce_cfactor_with_source_oriented_measures


class TestReduceCfactorWithSourceOrientedMeasures:
    """Class to test behaviour reduce C-factor reduction with source oriented
    measures"""

    c_factor = np.array([0.2, 0.8])
    c_reduction = np.array([0.5, 0.7])

    def test_reduce_values(self, recwarn):
        """Test reducing of value of C_factor with C_reduction. In addition test
        warning message from reduction.
        """
        c_factor_out = reduce_cfactor_with_source_oriented_measures(
            self.c_factor, self.c_reduction, True
        )
        np.testing.assert_almost_equal(c_factor_out, np.array([0.2 * 0.5, 0.8 * 0.3]))
        w = recwarn.pop(UserWarning)
        assert (
            str(w.message)
            == "Implementing source-oriented measures: reducing C-factor with "
            "value defined in '1 - C_reduction'."
        )

    def test_no_use_of_source_oriented_measures(self):
        """Test if the same C-factor valeus are obtained when not using
        reduction-functionality."""
        c_factor_out = reduce_cfactor_with_source_oriented_measures(
            self.c_factor, self.c_reduction, False
        )
        np.testing.assert_almost_equal(c_factor_out, np.array([0.2, 0.8]))

    def test_out_of_range_values(self):
        """Test whether an error is returned when the reduction-flag is on, and no
        C_reduction column is defined."""
        c_factor = np.array([0.2, 1.8])
        err_msg = "Values of c-factor should be between 0 and 1."
        with pytest.raises(IOError, match=err_msg):
            reduce_cfactor_with_source_oriented_measures(
                c_factor, self.c_reduction, True
            )

        c_reduction = np.array([0.2, 1.8])
        err_msg = "Values of c-reduction should be between 0 and 1."
        with pytest.raises(IOError, match=err_msg):
            reduce_cfactor_with_source_oriented_measures(
                self.c_factor, c_reduction, True
            )

        c_factor = np.array([0.2, np.nan])
        err_msg = "Values of c-factor should be between 0 and 1."
        with pytest.raises(IOError, match=err_msg):
            reduce_cfactor_with_source_oriented_measures(
                c_factor, self.c_reduction, True
            )

        c_reduction = np.array([0.2, np.nan])
        err_msg = "Values of c-reduction should be between 0 and 1."
        with pytest.raises(IOError, match=err_msg):
            reduce_cfactor_with_source_oriented_measures(
                self.c_factor, c_reduction, True
            )
