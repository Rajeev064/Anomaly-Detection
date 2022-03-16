import pandas as pd
from utils import (
    closest,
    get_numeric_range,
    pre_process,
    closest_number,
    std_similarity,
    is_valid_gtin,
    str_similarity,
)


class Scorer:
    brand_data = None
    row = None
    likely_brand = None

    default_column_names = {
        "product": "Product Name",
        "brand": "Manufacturer Name",
        "gtin": "Product GTIN",
        "mrp": "MRP",
        "net_weight": "Net Weight",
        "fssai": "Fssai Lic. No.",
    }

    def __init__(self):
        self.column_names = Scorer.default_column_names

    def train(self, df: pd.DataFrame):
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

        self.brand_data = brand_data

    def row_get(self, key):
        if self.row is None or key not in self.column_names:
            return None

        row = self.row
        mapped_key = self.column_names[key]

        return None if mapped_key not in row else row[mapped_key]

    def get_gtin_score(self):
        row = self.row

        if row is None:
            return {}

        return {"gtin_score": 1 if is_valid_gtin(self.row_get("gtin")) else 0}

    def get_alternate_brand_score(self):
        raise NotImplementedError

    def get_brand_score(self):
        row = self.row
        brand_data = self.brand_data
        if row is None or brand_data is None:
            return {}

        brand = self.row_get("brand")
        if not brand:
            return self.get_alternate_brand_score()

        brand = pre_process(brand)
        brand_score = 0
        likely_brand = ""
        if brand in brand_data:
            brand_score = 1
            likely_brand = brand
        else:
            likely_brand, brand_score = closest(brand, brand_data, str_similarity)

        if likely_brand in brand_data:
            self.likely_brand = likely_brand

        return {"likely_brand": likely_brand, "brand_score": brand_score}

    def get_product_score(self):
        row = self.row
        brand_data = self.brand_data
        likely_brand = self.likely_brand
        if row is None or brand_data is None or likely_brand is None:
            return {}
        products = brand_data[likely_brand]["products"]
        product = pre_process(self.row_get("product"))

        product_score = 0
        likely_product = ""
        if product in products:
            product_score = 1
            likely_product = product
        else:
            likely_product, product_score = closest(product, products, str_similarity)

        return {"likely_product": likely_product, "product_score": product_score}

    def get_numeric_score(self, key, row_key):
        row = self.row
        brand_data = self.brand_data
        likely_brand = self.likely_brand
        if row is None or brand_data is None or likely_brand is None:
            return {}

        val = closest_number(self.row_get(row_key))
        val_range = brand_data[likely_brand][key]
        val_score = std_similarity(val, val_range)

        return {
            f"{key}_score": val_score,
            f"likely_{key}": val,
            f"{key}_range": val_range,
        }

    def get_mrp_score(self):
        return self.get_numeric_score("mrp", "mrp")

    def get_net_weight_score(self):
        return self.get_numeric_score("net_weight", "net_weight")

    def get_weight_ratio_score(self, weight, mrp):
        row = self.row
        brand_data = self.brand_data
        likely_brand = self.likely_brand
        if row is None or brand_data is None or likely_brand is None:
            return {}

        ideal_ratio = brand_data[likely_brand]["weight_ratio"]
        ratio = weight / mrp
        if ratio == 0 and ideal_ratio == 0:
            return 1

        return {"weight_ratio_score": min(ratio, ideal_ratio) / max(ratio, ideal_ratio)}

    def __call__(self, row, column_names=None):
        """
        Currently Uses:
            Brand Name
            Product Name
            MRP
            Net Weight
        """
        self.likely_brand = None
        self.row = row

        self.column_names = (
            column_names if type(column_names) == dict else Scorer.default_column_names
        )

        brand_result = self.get_brand_score()
        product_result = self.get_product_score()
        net_weight_result = self.get_net_weight_score()
        mrp_result = self.get_mrp_score()
        weight_ratio_result = self.get_weight_ratio_score(
            net_weight_result["likely_net_weight"], mrp_result["likely_mrp"]
        )
        gtin_result = self.get_gtin_score()

        overall_score = (
            brand_result["brand_score"]
            + product_result["product_score"]
            + weight_ratio_result["weight_ratio_score"]
            + gtin_result["gtin_score"]
        ) / 4

        result = {
            **brand_result,
            **product_result,
            **net_weight_result,
            **mrp_result,
            **weight_ratio_result,
            **gtin_result,
            "overall_score": overall_score,
        }
        return result
