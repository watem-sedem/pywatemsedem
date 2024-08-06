import numpy as np
import pandas as pd


def process_cn_raster(
    hsg,
    parcels,
    season,
    composite_landuse,
    parcels_ids,
    cn_table,
    nodata=-9999,
):
    """Creates the CN-map for a given year and season.

    Current implementation executes three steps:

    - Generate a CNmaxID based on CN type id (1-11, associated to crop), contour
      plowing measures (0/1/2), hydrological conditions ({0,1->3},
      {unknown, poor to good}), contour_id (0/1).
    - Couple CN-values based in CNmaxID and season for all parcels (based on parcel id)
    - Coupled CN-values 99, 99 and 1 to land-uses river (-1) , infrastructure (-2) and
      water (-5).


    Parameters
    ----------
    hsg: numpy.ndarray
        Raster that holds values from 1 to 4 according to hydrological soil group
        (A, B, C and D), see [1]_ and [2]_, for more info, see documentation in function
        :attr: pywatemsedem.catchment.Catchment.hydrological_soil_group`.
    parcels: geopandas.GeoDataFrame
        Parcels polygon data with columns:

        - *NR* (int): unique id, should be the same as in parcels_ids (i.e. parcels_ids
          is a rasterized version of the parcels dataframe).
        - "CN_type_id" (int): crop specific CN id (1-11).
        - "HydroCond" (str): Either "Poor", "Fair" or "Good".

        Optional columns:

        - *gewasrest* (int): are the 'gewasresten' yes (1) or no (0).
        - *contour* (int): is contour plowing applied yes (1) or no (0).
        - *ntkerende* (int): is there non-plowing tillage yes (1) or no (0).
        - *verslemp* (int): has silting occurred yes (1) or no (0).

    season: str
        Either "fall", "spring", "summer", "winter"

    composite_landuse: numpy.ndarray
        A composite land-use raster. Typically, it defines the landuse from
        non-agricultural pixels.
    parcels_ids: numpy.ndarray
        A parcels id raster, holding unique id's per parcel.
    cn_table: pandas.DataFrame
        Table holding CNmax values per hydrological soil group and per CNmaxID.
    nodata: float, default -9999
        Nodata value

    Returns
    -------
    arr_cn: numpy.ndarray
        Raster with values between 1 (low CN, low run-off) and 100 (high CN,
        high run-off)


    Notes
    -----
    1. The CNtype_id is crop/cover-specific. Note that for general land-uses reported
       in the base landuse map (no crop info present), CN is set equal to a predefined
       CNmax:

       - forest: CN = CNmax is based on CNmaxID 9030
       - grassland: CN = CNmax is based on CNmaxID 5020
       - grass: CN = CNmax is based on CNmaxID 6000

    2. CN is set equal to 99 for infrastructure, rivers and pools (no infiltration)

    3. The contour_id is computed by:

        - contour_id = 1 if CNtype_id in {2, 3, 4} and contour = 0
        - contour_id = 2 if CNtype_id in {2, 3, 4} and contour = 1
        - contour_id = 0 else

    4. The HydroCond_id is computed by:

        - HydroCond_id = 1 if HydroCond is equal to 'Poor'.
        - HydroCond_id = 2 if HydroCond is equal to 'Fair'.
        - HydroCond_id = 3 if HydroCond is equal to 'Good'.
        - HydroCond_id = 0 if HydroCond is equal to NULL.

    5. Gewasrest_id is equal to gewasrest (1 or 0)

    6. When the CNtype_id is equal to NULL, CNtype_id is set to 4,
       HydroCond_id to 1 and contour_id to 1.


    References
    ----------
    .. [1] NRCS, 2004. Hydrologic soil-cover complexes (chapter 9).
    .. [2] NRCS, 2009. Hydrologic soil groups (chapter 7).
    """
    if season not in ["summer", "spring", "winter", "fall"]:
        msg = "Season should be 'summer', 'spring', 'winter' and 'fall'."
        raise ValueError(msg)

    df = parcels.copy()
    # standard set contour-source-oriented measures off
    if "contour" not in df:
        df["contour"] = 0
    # maak een contour_id per perceel op basis van het CN-type (1-11) en
    # de contouroptie van de percelen
    df["contour_id"] = 0  # standaardwaarde
    cond = df["CNtype_id"].isin([2, 3, 4]) & df["contour"].isin(
        [0]
    )  # CNtype 2,3 of 4 en geen contourploegen
    df["contour_id"] = np.where(cond, 1, df["contour_id"])  # contour_id krijgt 1 (SR)
    cond = df["CNtype_id"].isin([2, 3, 4]) & df["contour"].isin(
        [1]
    )  # CNtype 2,3 of 4 en contourploegen
    df["contour_id"] = np.where(cond, 2, df["contour_id"])  # contour_id krijgt 2 (C)

    # hydrologische toestand van de bodem op het perceel
    df["HydroCond_id"] = 0  # standaardwaarde
    df["HydroCond_id"] = np.where(df["HydroCond"] == "Poor", 1, df["HydroCond_id"])
    df["HydroCond_id"] = np.where(df["HydroCond"] == "Fair", 2, df["HydroCond_id"])
    df["HydroCond_id"] = np.where(df["HydroCond"] == "Good", 3, df["HydroCond_id"])

    # gewasrest
    if "gewasrest" not in df:
        df["gewasrest"] = 0
    df["gewasrest_id"] = np.where(df["gewasrest"] == 1, 1, 0)

    # zet alle percelen waar geen gegevens (onbekende teelt) voor zijn
    # op onbekend
    cond = df["CNtype_id"].isnull()
    df["CNtype_id"] = np.where(cond, 4, df["CNtype_id"])
    df["HydroCond_id"] = np.where(cond, 1, df["HydroCond_id"])
    df["contour_id"] = np.where(cond, 1, df["contour_id"])

    df["CNmaxID"] = (
        df["CNtype_id"].astype(int).map(str)
        + df["contour_id"].map(str)
        + df["HydroCond_id"].map(str)
        + df["gewasrest_id"].map(str)
    )
    df["CNmaxID"] = df["CNmaxID"].astype(int)
    df = pd.merge(df, cn_table, how="left", on="CNmaxID")

    # correctiefactoren cover en verslemping
    # geen gegevens, dus 0 --> geen correctie bij berekening CN

    # Voorlopige invulling seizoensafhankelijkheid CN -->
    # cijfers gebaseerd op bedekkingsgraad van 15 veelvoorkomende gewassen
    # (cover.txt), behoorlijk hoge bedekkingsgraden in winter te wijten aan
    # groot aandeel grasland binnen de Vlaamse percelen
    cover_seasons = np.array([40.1919, 52.3333, 80.7869, 47.4675])

    if season == "winter":
        df["cover"] = cover_seasons[0]
    elif season == "spring":
        df["cover"] = cover_seasons[1]
    elif season == "summer":
        df["cover"] = cover_seasons[2]
    elif season == "fall":
        df["cover"] = cover_seasons[3]

    df["verslemp"] = 0

    arr_soil_classes = np.unique(
        hsg.astype(int)
    ).tolist()  # de arr_soil_classes aanwezig in het modelgebied
    arr_soil_classes = [cl for cl in arr_soil_classes if cl != nodata]
    # voor elk perceel wordt voor elke soil_class de CN-waarde berekend
    c2 = 3
    for soil_class in arr_soil_classes:
        cn_min = f"CNmin_{int(soil_class)}"
        cn_max = f"CNmax_{int(soil_class)}"
        c1 = f"c1_{int(soil_class)}"
        cn_model = f"CNmodel_{int(soil_class)}"
        df[cn_min] = 4.2 * df[cn_max] / (10 - 0.058 * df[cn_max])
        df[c1] = df[cn_max] - df[cn_min]
        df[cn_model] = (
            df[cn_max] - ((df["cover"] / 100) * df[c1]) + ((df["verslemp"] / 5) * c2)
        )
        # correctie niet kerende bodembewerking
        if "ntkerend" not in df:
            df["ntkerend"] = 0
        df[cn_model] = np.where(df["ntkerend"] == 1, df[cn_model] - 1, df[cn_model])

    # reclass perceelskaart --> kan beter! df.apply?
    arr_cn = np.ones(parcels_ids.shape) * nodata

    for row in df.itertuples():
        rstval = getattr(row, "NR")
        for soil_class in arr_soil_classes:
            newval = getattr(row, f"CNmodel_{int(soil_class)}")
            cond = np.logical_and(
                (parcels_ids == rstval),
                (hsg.astype(int) == soil_class),
            )
            arr_cn = np.where(cond, newval, arr_cn)

    # rivier, infrastructuur,  die niet op de landbouwperceelskaart staan.
    # waar geen percelen zijn moeten we opvullen op basis van landgebruik.
    arr_cn = np.where((composite_landuse == -1), 99, arr_cn)
    arr_cn = np.where(
        (composite_landuse == -2), 99, arr_cn
    )  # wegen en water krijgen CN 99
    arr_cn = np.where(
        (composite_landuse == -5), 0, arr_cn
    )  # vijvers en poelen krijgen CN 0

    # bossen, weiden en grasland die niet op de landbouwperceelskaart staan.
    # waar geen percelen zijn moeten we opvullen op basis van landgebruik.

    cn_table.index = cn_table["CNmaxID"]
    for soil_class in arr_soil_classes:
        cond = arr_cn == nodata
        z = cn_table[f"CNmax_{int(soil_class)}"].loc[9030]
        arr_cn[(cond) & (composite_landuse == -3) & (hsg.astype(int) == soil_class)] = z
        cond = arr_cn == nodata
        z = cn_table[f"CNmax_{int(soil_class)}"].loc[5020]
        arr_cn[(cond) & (composite_landuse == -4) & (hsg.astype(int) == soil_class)] = z
        cond = arr_cn == nodata
        z = cn_table[f"CNmax_{int(soil_class)}"].loc[6000]
        arr_cn[(cond) & (composite_landuse == -6) & (hsg.astype(int) == soil_class)] = z

    arr_cn[(parcels_ids == -9999) & (composite_landuse > 0)] = np.mean(
        arr_cn[(arr_cn >= 0) & (arr_cn <= 100)]
    )
    # !!!!!!! VOORLOPIGE FIX OM TE HOGE CN WAARDEN TE VERMIJDEN
    arr_cn[arr_cn > 100] = np.mean(arr_cn[(arr_cn >= 0) & (arr_cn <= 100)])
    arr_cn[arr_cn == nodata] = np.mean(arr_cn[(arr_cn >= 0) & (arr_cn <= 100)])

    return arr_cn, df
