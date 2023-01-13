import os

os.chdir("D:\\Users\\postvi\\Documents\\github\\wadi")

import wadi as wd

wdo = wd.DataObject(log_fname="messy_data.log", silent=True)

rows2skip = list(range(8)) + [21, 22] + list(range(24, 34))
df0_kwargs = {
    "skiprows": rows2skip,
    "usecols": "B:D",
    "datatype": "sampleinfo",
}

rows2skip = list(range(2)) + list(range(3, 9)) + [21, 22]
df1_kwargs = {
    "skiprows": rows2skip,
    "usecols": "E:AE",
    "units_row": 3,
    "datatype": "feature",
    "na_values": [999],
}

rows2skip = list(range(7)) + [8, 21, 22]
df2_kwargs = {
    "skiprows": rows2skip,
    "usecols": "AF",
    "datatype": "sampleinfo",
}

wdo.file_reader(
    file_path="docs/messy_data.xlsx",
    format="wide",
    blocks=[df0_kwargs, df1_kwargs, df2_kwargs],
)

# wdo.df.head()

feature_dict = wd.MapperDict(
    {
        "Phosphate": "PO4",
        "Nitrate": "NO3",
        "Nitrite": "NO2",
        "Ammonium": "NH4",
        "Silica": "SiO2",
        "Sulphate": "SO4",
        "Sodium": "Na",
        "Calcium": "Ca",
        "Arsenic": "As",
    }
)

wdo.name_map(
    m_dict=feature_dict,
    match_method=["exact", "fuzzy"],
)

wdo.unit_map(
    match_method=["regex"],
    replace_strings={"μ": "u", "-": " ", "%": "percent"},
)

merge_cols = [
    ["Phosphate", "Phosphate.1"],
    ["Nitraat", "Nitrate"],
    ["Nitrite", "Nitrite.1"],
    ["Ammonium", "Ammonium.1"],
    ["Silica", "Silica.1"],
    ["Sulphate", "Sulphate.1"],
    ["Calcium", "Calcium.1"],
    ["Arsenic", "Arsenic.1"],
    ["Electrical Conductivity", "ec"],
    ["E.coli", "E.coli.1"],
]

drop_cols = [
    "SampleID",
    "Unnamed: 17",
]

override_units = {
    "Arsenic": "umol/l",
    "Arsenic.1": "umol/l",
    "ec": "µS/cm",
}

df = wdo.harmonizer(
    merge_columns=merge_cols,
    drop_columns=drop_cols,
    convert_units=True,
    target_units="mmol/l",
    override_units=override_units,
)

df = wdo.get_frame()

print(df.head())

print(df["As"].head())

df.to_excel("wadi_output/tidied_data.xlsx")
