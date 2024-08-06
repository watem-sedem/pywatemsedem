from pathlib import Path

import numpy as np
import pandas as pd

from pywatemsedem.geo.utils import load_raster
from pywatemsedem.io.modeloutput import load_total_sediment_file


def _compare_folder(
    folder_benchmark,
    folder_output,
    year="2018",
    name="molenbeek",
    scenario="scenario_1",
):
    """Compare the setup of the folder/file structure

    Notes
    -----
    The filecmp, https://docs.python.org/3/library/filecmp.html, is not used
    as the file
    content can differ with a given precision on value-level. This functions
    checks
    which files/folders, specific functions are defined to test the data
    content.
    """

    # Check main folder is user defined name
    assert _get_subdir_names(folder_benchmark) == _get_subdir_names(folder_output)

    # Check data and catchment subfolders
    assert _get_subdir_names(folder_benchmark / name).issuperset(
        _get_subdir_names(folder_output / name)
    )
    assert {"Data_Bekken", scenario}.issubset(_get_subdir_names(folder_output / name))

    # Check scenario subfolders
    assert sorted(_get_subdir_names(folder_output / name / scenario)) == sorted(
        {str(year), "modelinput", "modeloutput", "postprocessing"}
    )

    # check 'modelinput' files
    assert sorted(
        _get_filenames(folder_benchmark / name / scenario / "modelinput")
    ) == sorted(_get_filenames(folder_output / name / scenario / "modelinput"))

    # check 'modeloutput' files
    assert sorted(
        _get_filenames(folder_benchmark / name / scenario / "modeloutput")
    ) == sorted(_get_filenames(folder_output / name / scenario / "modeloutput"))

    # check 'Data_bekken' files
    assert sorted(_get_filenames(folder_benchmark / name / "Data_Bekken")) == sorted(
        _get_filenames(folder_output / name / "Data_Bekken")
    )
    # check 'year' files
    assert sorted(
        _get_filenames(folder_benchmark / name / scenario / str(year))
    ) == sorted(_get_filenames(folder_output / name / scenario / str(year)))


def _compare_rst(
    folder_benchmark,
    folder_output,
    year="2018",
    name="molenbeek",
    scenario="scenario_1",
    ext=".rst",
    to_check_folders=["modelinput", "modeloutput"],
):
    """rst files in input and outfolder should be the same"""
    for folder in to_check_folders:
        _compare_rst_folder(
            folder_benchmark / name / scenario / folder,
            folder_output / name / scenario / folder,
            ext,
        )


def _compare_rst_folder(ref, new, ext=".rst"):
    """Compare RST files in two folders"""

    for file_name in ref.glob(f"*{ext}"):

        # adjust the numerical tolerance as function of the data; cumulative
        # data need to have more relative tolerance
        # TODO sgobeyn/daanr - revise these categories
        if file_name.name in [
            f"WATEREROS (mm per gridcel){ext}",
            f"RUSLE{ext}",
            f"Capacity{ext}",
            f"SediExport_kg{ext}",
            f"SediIn_kg{ext}",
            f"SLOPE{ext}",
        ]:
            rtol, atol = 1e-5, 1e-3
        elif file_name.name in [f"WATEREROS (kg per gridcel){ext}"]:
            rtol, atol = 1e-4, 1e-3
        elif file_name.name in [
            f"LS{ext}",
            f"AspectMap{ext}",
            f"sewer_in{ext}",
            f"cumulative{ext}",
            f"UPAREA{ext}",
            f"SediOut_kg{ext}",
        ]:
            rtol, atol = 1e-5, 1e-8
        else:
            rtol, atol = 1e-8, 1e-8
        equal_rst(
            file_name,
            (new / file_name.name),
            rtol=rtol,
            atol=atol,
        )


def _compare_table(
    folder_benchmark,
    folder_output,
    year="2018",
    name="molenbeek",
    scenario="scenario_1",
    to_check_folders=["modelinput", "modeloutput"],
):
    """rst files in input and outfolder should be the same"""

    for folder in to_check_folders:
        for file_name in (folder_benchmark / name / scenario / folder).glob("*.txt"):
            if file_name.name == "Total sediment.txt":
                equal_total_sediment(
                    file_name,
                    (folder_output / name / scenario / folder / file_name.name),
                    rtol=1e-8,
                    atol=1e-8,
                )
            elif file_name.name == "Total sediment VHA.txt":
                equal_table(
                    file_name,
                    (folder_output / name / scenario / folder / file_name.name),
                    rtol=1e-8,
                    atol=1e-8,
                    skiplines=1,
                )
            else:
                equal_table(
                    file_name,
                    (folder_output / name / scenario / folder / file_name.name),
                    rtol=1e-8,
                    atol=1e-8,
                    skiplines=0,
                )


def serialize_process_raster(rst):
    """Serializer function for rasters

    Parameters
    ----------
    rst: pathlib.path or str
        File path of to-assert raster

    Returns
    -------
    function:
        Return function that processes numpy array of pywatemsedem raster.
    """
    if "perceelskaart" in Path(rst).stem:
        return process_arr_cnwsperceelskaart
    else:
        return process_arr_default


def process_arr_cnwsperceelskaart(arr):
    """Remove unique parcels id's before comparing rasters

    Parameters
    ----------
    arr: np.ndarray
        WaTEM/SEDEM perceelskaart array to preprocess before moving to an assert
        statement.

    Returns
    -------
    arr: np.ndarray
        Processed WaTEM/SEDEM perceelskaart array to preprocess before moving to an
        assert statement.
    """
    arr[arr > 0] = 1
    return arr


def process_arr_default(arr):
    """Dummy function for processing arr

    Parameters
    ----------
    arr: np.ndarray
        Array to preprocess before moving to an assert statement.

    Returns
    -------
    arr: np.ndarray
        Equal to input.
    """
    return arr


def equal_ini(inifile_1, inifile_2, skip_lines=[1, 4, 5, 10]):
    """Check if settings.ini files are the same.

    Ignore difference in filepath and date
    lines [1, 4, 5, 10] contain paths and dates which are not compared

    Parameters
    ----------
    inifile_1: str or pathlib.Path
        File path of first ini-file.
    inifile_2: str or pathlib.Path
        File path of first ini-file.
    skip_lines: list
        Lines to skip in ini-file"""
    with open(inifile_1) as ini_1:
        with open(inifile_2) as ini_2:
            ini_content_1 = [
                line
                for idx, line in enumerate(ini_1.readlines())
                if idx not in skip_lines
            ]
            ini_content_2 = [
                line
                for idx, line in enumerate(ini_2.readlines())
                if idx not in skip_lines
            ]
            assert ini_content_1 == ini_content_2
            assert set(ini_content_1).difference(set(ini_content_2)) == set()


def equal_table(txt_table_file_1, txt_table_file_2, rtol=1e-8, atol=1e-8, skiplines=0):
    """Check if table data are the same

    Parameters
    ----------
    txt_table_file_1: str or pathlib.Path
        File path of first table-like file.
    txt_table_file_2: str or pathlib.Path
        File path of second table-like file.
    rtol: float
        See :func:`numpy.testing.assert_allclose`.
    atol: float
        See :func:`numpy.testing.assert_allclose`.
    skiplines: int
        See :func:`pandas.read_csv`.
    """
    tbl_1 = pd.read_csv(txt_table_file_1, skiprows=skiplines, delimiter="\t")
    tbl_2 = pd.read_csv(txt_table_file_2, skiprows=skiplines, delimiter="\t")
    pd.testing.assert_frame_equal(tbl_1, tbl_2, rtol=rtol, atol=atol)


def equal_total_sediment(
    txt_total_sediment_file_1, txt_total_sediment_file_2, rtol=1e-8, atol=1e-8
):
    """Check if total sediment output data of two files are the same

    Parameters
    ----------
    txt_total_sediment_file_1: str or pathlib.Path
        File path to WaTEM/SEDEM total sediment output file 1.
    txt_total_sediment_file_2: str or pathlib.Path
        File path to WaTEM/SEDEM total sediment output file 2.
    rtol: float
        See :func:`numpy.testing.assert_allclose`.
    atol: float
        See :func:`numpy.testing.assert_allclose`.
    """
    sed1 = load_total_sediment_file(txt_total_sediment_file_1)
    sed2 = load_total_sediment_file(txt_total_sediment_file_2)
    for val1, val2 in zip(sed1.values(), sed2.values()):
        assert np.allclose(val1, val2, rtol=rtol, atol=atol)


def equal_rst(rst_file_1, rst_file_2, rtol=1e-8, atol=1e-8):
    """Check if content of raster files are equal.

    Parameters
    ----------
    rst_file_1: pathlib.path
        File path of first raster.
    rst_file_2: pathlib.path
        File path of  second raster
    rtol: float
        See :func:`numpy.testing.assert_allclose`.
    atol: float
        See :func:`numpy.testing.assert_allclose`.
    """
    condition, _, _ = check_equal_rst(rst_file_1, rst_file_2, rtol, atol)

    if not condition:
        msg = f"Content {rst_file_1.stem} not equal to content " f"{rst_file_2.stem}."
        raise AssertionError(msg)


def check_equal_rst(rst_file_1, rst_file_2, rtol=1e-8, atol=1e-8):
    """Check if content of raster files are equal.

    Parameters
    ----------
    rst_file_1: pathlib.path
        File path of first raster.
    rst_file_2: pathlib.path
        File path of  second raster
    rtol: float
        See :func:`numpy.testing.assert_allclose`.
    atol: float
        See :func:`numpy.testing.assert_allclose`.

    """
    arr1, profile = load_raster(rst_file_1)
    arr2, profile = load_raster(rst_file_2)

    condition = np.allclose(arr1, arr2, rtol=rtol, atol=atol, equal_nan=True)

    return condition, arr1, arr2


def _get_subdir_names(path):
    """"""
    return set([item.name for item in path.iterdir() if item.is_dir()])


def _get_filenames(path):
    """"""
    return set(
        [
            item.name
            for item in path.iterdir()
            if (item.suffix in [".tif", ".rst", ".shp"])
        ]
    )


def _compare_cnws_input_raster(
    rst,
    rst_benchmark,
    tag,
    rtol=1e-8,
    atol=1e-8,
):
    """Compare two WaTEM/SEDEM rasters

    Check if they are equal, and if not, raise an Assertion with relevant statistics
    about difference. The statistics are dependent on the substansive content of the
    file.


    Parameters
    ----------
    rst: str or pathlib.Path
        File path of raster from test simulation
    rst_benchmark: str or pathlib.Path
        File path of raster from benchmark simulation
    rtol: float
    atol: float
    """
    condition, arr, arr_benchmark = check_equal_rst(rst, rst_benchmark, rtol, atol)

    if not condition:

        if tag.lower() in ["perceelskaart"]:
            out = compute_difference_table_cnws_prckrt_rasters(arr, arr_benchmark)
        elif tag.lower() in ["c-factor", "ktc"]:
            out = compute_difference_table_cnws_rasters(arr, arr_benchmark, tag)
        elif tag.lower() in ["buffers"]:
            out = compute_difference_table_cnws_buffers(arr, arr_benchmark)
        else:
            msg = f"``tag`` {tag} not known."
            raise IOError(msg)

        msg = (
            f"WaTEM/SEDEM '{tag}' rasters are not equal. Difference statistics table: "
            f"\n {out}"
        )
        raise AssertionError(msg)


def compute_difference_table_cnws_buffers(arr, arr_benchmark, buf_idext=2**14):
    """Compute table whcih indicates difference between two WaTEM/SEDEM buffer raster
    files.


    Parameters
    ----------
    arr: np.ndarray
    arr_benchmark: np.ndarray
    buf_idext: float
        Threshold value that differentiates in buffer raster which is a buffer_id and
        which is a buffer extension id, SEE XXX

    Returns
    -------
    str:
        String format of difference dataframe table.
    """
    n_buffers = np.unique(arr[arr <= buf_idext]).shape[0]
    n_buffers_benchmark = np.unique(arr_benchmark[arr_benchmark <= buf_idext]).shape[0]

    n_buffers_exid = np.unique(arr[arr > buf_idext]).shape[0]
    n_buffers_exid_benchmark = np.unique(
        arr_benchmark[arr_benchmark > buf_idext]
    ).shape[0]

    return pd.DataFrame(
        data=[
            [n_buffers, n_buffers_benchmark],
            [n_buffers_exid, n_buffers_exid_benchmark],
        ],
        columns=["test", "benchmark"],
        index=["n_buf_id", "n_buf_exid"],
    ).to_string()


def compute_difference_table_cnws_rasters(arr, arr_benchmark, tag):
    """Compute table whcih indicates difference between two WaTEM/SEDEM raster files.

    Parameters
    ----------
    arr: np.ndarray
    arr_benchmark: np.ndarray

    Returns
    -------
    str:
        String format of difference dataframe table.
    """
    arr_diff = arr - arr_benchmark

    return (
        pd.DataFrame(arr_diff[arr_diff != 0], columns=[f"diff_{tag}"])
        .describe()
        .to_string()
    )


def compute_difference_table_cnws_prckrt_rasters(
    arr,
    arr_benchmark,
    dict_translation={
        -6: "grass strips",
        -5: "pool",
        -4: "meadow",
        -3: "forest",
        -2: "infrastructure",
        -1: "river",
        0: "outside_domain",
        1: "agriculture",
    },
    res=20,
):
    """Compute table whcih indicates difference between two WaTEM/SEDEM
    perceelskaart raster files.

    Parameters
    ----------
    arr: np.ndarray
    arr_benchmark: np.ndarray

    Returns
    -------
    str:
        String format of difference dataframe table.
    """
    df = pd.DataFrame(columns=["left", "right"])
    df["test"] = arr.ravel()
    df["benchmark"] = arr_benchmark.ravel()
    df.loc[df["test"] > 0, "test"] = 1
    df.loc[df["benchmark"] > 0, "benchmark"] = 1
    df = df.replace(dict_translation)
    df["area (ha)"] = res**2 / 100**2
    df = df.groupby(["test", "benchmark"]).aggregate({"area (ha)": np.sum})

    return df.sort_values("area (ha)", ascending=False).to_string()
