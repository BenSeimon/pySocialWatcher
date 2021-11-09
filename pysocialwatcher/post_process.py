import numpy as np
import pandas as pd
from itertools import product
import ast


def process_age(x):
    s = ast.literal_eval(x)
    min_age = "" if "min" not in s else str(s["min"])
    max_age = "" if "max" not in s else str(s["max"])
    age_string = "%s-%s" % (min_age, max_age)

    return pd.Series({"MinAge": None if min_age == "" else min_age,
                      "MaxAge": None if max_age == "" else max_age,
                      "Ages": age_string})


def process_location(x):
    s = ast.literal_eval(x)
    keys, regions, region_ids, names, country_codes, loctype, fullloc = [], [], [], [], [], [], []

    loc_type = s["name"]

    if loc_type == "cities":
        cities = s["values"]
        # Multiple cities are not supported ***yet***
        for city in cities:
            loctype.append("city")
            keys.append(city["key"])
            regions.append(city["region"])
            region_ids.append(city["region_id"])
            names.append(city["name"])
            country = city["country_code"] if "country_code" in city else city["country"] if "country" in city else None
            country_codes.append(country)
            fullloc.append("%s, %s, %s" % (city["name"], city["region"], country))

    elif loc_type == "regions":
        regs = s["values"]
        # Multiple regions are not supported ***yet***
        for region in regs:
            loctype.append("region")
            keys.append(region["key"])
            regions.append(region["name"])
            region_ids.append(region["key"])
            names.append(region["name"])
            country = region["country_code"] if "country_code" in region else region["country"] if "country" in region else None
            country_codes.append(country)
            fullloc.append("%s, %s" % (region["name"], country) if country else "%s" % region["name"])

    elif loc_type == "countries":
        countries = s["values"]
        # Multiple regions are not supported ***yet***
        for country in countries:
            loctype.append("country")
            keys.append(country)
            regions.append(None)
            region_ids.append(None)
            names.append(country)
            country_codes.append(country)
            fullloc.append(country)

    elif loc_type == "custom_locations":
        locations = s["values"]
        for loc in locations:
            loctype.append("custom")
            keys.append(loc["name"])
            regions.append(None)
            region_ids.append(None)
            country = "country_code" if "country_code" in loc else "country" if "country" in loc else None
            names.append(loc["name"])
            country_codes.append(country)
            fullloc.append(loc["name"])

    keys = ', '.join(filter(None, keys)) if len(keys) > 1 else keys[0]
    regions = ', '.join(filter(None, regions)) if len(regions) > 0 else regions[0]
    region_ids = ', '.join(map(str,filter(None, region_ids))) if len(region_ids) > 0 else region_ids[0]
    names = ', '.join(filter(None, names)) if len(names) > 0 else names[0]
    country_codes = ', '.join(filter(None, country_codes)) if len(country_codes) > 0 else country_codes[0]
    loctype = ', '.join(filter(None, loctype)) if len(loctype) > 0 else loctype[0]
    fullloc = ', '.join(filter(None, fullloc)) if len(fullloc) > 0 else fullloc[0]

    names = s["pySocialWatcherReference"] if "pySocialWatcherReference" in s else names

    return pd.Series({"Key": keys, "Region": regions, "RegionId": region_ids,
                      "Name": names, "CountryCode": country_codes,
                      "LocationType": loctype, "FullLocation": fullloc})


def process_device(x):
    if isinstance(x, float) and np.isnan(x):
        return "AllDevices"
    s = ast.literal_eval(x)
    return s["name"] if "name" in s else None


def process_scholarities(x):
    if isinstance(x, float) and np.isnan(x):
        return "AllDegrees"
    s = ast.literal_eval(x)
    return s["name"] if "name" in s else None


def process_citizenship(x):
    if isinstance(x, float) and np.isnan(x):
        return "AllCitizens"
    s = ast.literal_eval(x)
    return s["name"] if "name" in s else None


def process_languages(x):
    if isinstance(x, float) and np.isnan(x):
        return "AllLanguages"
    s = ast.literal_eval(x)
    return s["name"] if "name" in s else None


def post_process_df_collection(df):

    # Process gender information
    gender = df["genders"].apply(lambda x: {0: "both", 1: "male", 2: "female"}[x])
    df["Gender"] = gender

    # Process access device, if available
    if "access_device" in df:
        device = df["access_device"].apply(lambda x: process_device(x))
        df["Device"] = device

    # Process age information
    ages = df["ages_ranges"].apply(lambda x: process_age(x))
    df = pd.merge(df, ages, left_index=True, right_index=True)

    # Process location information
    locations = df["geo_locations"].apply(lambda x: process_location(x))
    df = pd.merge(df, locations, left_index=True, right_index=True)

    # Process education tag if information is available
    if "scholarities" in df:
        device = df["scholarities"].apply(lambda x: process_scholarities(x))
        df["Education"] = device

    # Process citizenship tag if information is available
    if "citizenship" in df:
        citizenship = df["citizenship"].apply(lambda x: process_citizenship(x))
        df["Citizenship"] = citizenship

    # Process language tag if information is available
    if "languages" in df:
        languages = df["languages"].apply(lambda x: process_languages(x))
        df["Languages"] = languages

    # TODO: process other possible fields

    drop_cols = ["genders"]
    df = df.drop(columns=drop_cols)

    return df


def combine_cols(df_in, cols, input_cols=["Key", "mau_audience"], output_col="combo"):
    unique_values = []

    df = df_in[[*cols, *input_cols]].copy()

    # We first get the unique values for each one of the cols
    for c in cols:
        dfcut = df[c].unique()
        unique_values.append(dfcut)

    results = []

    # We generate their combinations
    for combo in product(*unique_values):
        combo_string = "_".join(combo)
        # print(combo_string)

        dfcut = df.copy()

        for c, v in zip(cols, combo):
            dfcut = dfcut[dfcut[c] == v]

        dfcut = dfcut.drop(columns=cols)
        dfcut[output_col] = combo_string
        results.append(dfcut)

    return pd.concat(results).reset_index(drop=True)
