import math
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

from tqdm import tqdm


class Scorer:
    brand_data = None
    row = None
    likely_brand = None

    fssai_map = {}
    contact_email_map = {}

    all_products = set()

    default_column_names = {
        "product": "Product Name",
        "brand": "Company Name",
        "gtin": "GTIN",
        "mrp": "MRP",
        "net_weight": "Net Weight",
        "fssai": "FSSAI Lic No.",
        "contact_email": "Consumer Care Email",
    }

    DISCREET_SCALE_BY = 0.37

    def __init__(self):
        self.column_names = Scorer.default_column_names

    def make_map(self, map, key):
        for brand, brand_data in self.brand_data.items():
            map[brand_data[key]] = brand

    def train(self, df: pd.DataFrame):
        groups = df.groupby(self.column_names["brand"])
        brand_data = {}

        for brand, brand_df in tqdm(groups):
            brand_name = pre_process(brand)
            data = {
                "products": set(
                    brand_df[self.column_names["product"]].map(pre_process).unique()
                ),
                "net_weight": get_numeric_range(
                    brand_df[self.column_names["net_weight"]]
                ),
                "mrp": get_numeric_range(brand_df[self.column_names["mrp"]]),
            }
            fssai = brand_df[brand_df[self.column_names["fssai"]].str.len() > 10][
                self.column_names["fssai"]
            ].mode()

            self.all_products.update(
                brand_df[self.column_names["product"]].map(pre_process).unique()
            )

            data["fssai"] = fssai.iloc[0] if len(fssai) > 0 else None
            contact_email = (
                brand_df[self.column_names["contact_email"]].mode()
                if self.column_names["contact_email"] in brand_df
                else None
            )
            data["contact_email"] = (
                (contact_email.iloc[0] if len(contact_email) > 0 else None)
                if contact_email
                else None
            )
            data["weight_ratio"] = (
                brand_df[self.column_names["net_weight"]]
                / brand_df[self.column_names["mrp"]]
            ).mean()

            brand_data[brand_name] = data

        self.brand_data = brand_data
        self.make_map(self.fssai_map, "fssai")
        self.make_map(self.contact_email_map, "contact_email")

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

    def get_alternate_brand_score(self, row_key, map):

        val = pre_process(self.row_get(row_key))

        if not val:
            return {
                "likely_brand": None,
                "brand_score": -1,
                "brand_resolution": row_key,
                "brand_resolved_value": val,
            }

        likely_brand, brand_score, likely_val = None, 0, val

        if val in map:
            likely_brand = map[val]
            brand_score = 1
        else:
            likely_val, brand_score = closest(val, map, str_similarity)
            likely_brand = map[likely_val]

        if likely_brand:
            self.likely_brand = likely_brand

        return {
            "likely_brand": likely_brand,
            "brand_score": brand_score,
            "brand_resolution": row_key,
            "brand_resolved_value": val,
        }

    def get_brand_score(self):
        row = self.row
        brand_data = self.brand_data
        if row is None or brand_data is None:
            return {}

        brand = self.row_get("brand")

        if not brand:
            return self.get_alternate_brand_score(
                "contact_email", self.contact_email_map
            )

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
        if row is None or brand_data is None:
            return {}

        products = (
            self.all_products
            if likely_brand is None
            else brand_data[likely_brand]["products"]
        )
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
        if row is None or brand_data is None:
            return {}

        val = closest_number(self.row_get(row_key))
        val_range = brand_data[likely_brand][key] if likely_brand else None

        score = -1

        if val_range:
            if val_range["min"] <= val and val_range["max"] >= val:
                score = 1
            else:
                score = 0

        return {
            f"{key}_score": score,
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
        if row is None or brand_data is None or likely_brand is None or mrp == 0:
            return {"weight_ratio_score": -1}

        ideal_ratio = brand_data[likely_brand]["weight_ratio"]
        ratio = weight / mrp
        if ratio == 0 and ideal_ratio == 0:
            return 1

        score = min(ratio, ideal_ratio) / max(ratio, ideal_ratio)
        if math.isnan(score):
            score = 0
        return {"weight_ratio_score": score}

    def __call__(self, row, column_names=None):
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

        brand_score = brand_result["brand_score"]
        product_score = product_result["product_score"]

        weight_ratio_score = weight_ratio_result["weight_ratio_score"]
        gtin_score = gtin_result["gtin_score"]
        mrp_score = mrp_result["mrp_score"]
        net_weight_score = net_weight_result["net_weight_score"]

        overall_score = 0
        params_used = 0

        if product_score <= 0.7:
            overall_score = 0
        else:
            useable = [
                {"score": net_weight_score, "type": "discreet"},
                {"score": mrp_score, "type": "discreet"},
                {"score": gtin_score, "type": "discreet"},
                {"score": product_score, "type": "continuous"},
            ]

            if brand_score >= 0:
                useable += [
                    {"score": brand_score, "type": "continuous"},
                    {"score": weight_ratio_score, "type": "discreet"},
                ]

            for idx, score in enumerate(useable):
                if score["score"] < 0:
                    useable.pop(idx)

            # Too little data
            if len(useable) <= 2:
                overall_score = 0

            num, denom = 0, 0

            for score in useable:
                scale = Scorer.DISCREET_SCALE_BY if score["type"] == "discreet" else 1

                num += score["score"] * scale
                denom += scale

            overall_score = num / denom
            params_used = len(useable)

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
