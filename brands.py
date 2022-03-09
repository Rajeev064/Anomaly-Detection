import pandas as pd

from utils import pre_process


def get_numeric_range(series: pd.Series):
    return {
        "std": series.std(),
        "mean": series.mean(),
        "median": series.median(),
        "min": series.min(),
        "max": series.max(),
    }


def get_brand_data(df: pd.DataFrame) -> dict:
    groups = df.groupby("Manufacturer Name")
    brand_data = {}

    for brand, brand_df in groups:
        brand_name = pre_process(brand)
        data = {
            "products": set(brand_df["Product Name"].map(pre_process).unique()),
            "net_weight": get_numeric_range(brand_df["Net Weight"]),
            "mrp": get_numeric_range(brand_df["MRP"]),
        }
        fssai = brand_df["Fssai Lic. No."].mode()
        data["fssai"] = fssai.iloc[0] if len(fssai) > 0 else None
        data["weight_ratio"] = (brand_df["Net Weight"] / brand_df["MRP"]).mean()

        brand_data[brand_name] = data

    return brand_data
