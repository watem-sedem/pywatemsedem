from conftest import calibratedata

from pywatemsedem import calibrate


class TestCalibrate:
    """Test class to test calibrate functionlaities."""

    # TODO: expand tests with dummy data.
    def test_process_calibrationrun_output(self):
        """Test processing of calibration output"""
        # implicit test
        calibrate.process_calibrationrun_output(
            calibratedata.txt_calibrate,
            1000,
            "test_catch",
            50 * 1000**2,
            endpoint_coefficient=0.0,
        )
