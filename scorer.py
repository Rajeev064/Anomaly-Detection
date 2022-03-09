from gtin import is_valid_gtin
from utils import closest, pre_process, closest_number, std_similarity
from edit_distance import similarity


class Scorer:
    brand_data = None
    row = None
    likely_brand = None

    def __init__(self, brand_data):
        self.brand_data = brand_data

    def get_gtin_score(self):
        row = self.row

        if row is None:
            return {}

        return {"gtin_score": 1 if is_valid_gtin(row["Product GTIN"]) else 0}

    def get_brand_score(self):
        row = self.row
        brand_data = self.brand_data
        if row is None or brand_data is None:
            return {}

        brand = pre_process(row["Manufacturer Name"])
        brand_score = 0
        likely_brand = ""
        if brand in brand_data:
            brand_score = 1
            likely_brand = brand
        else:
            likely_brand, brand_score = closest(brand, brand_data, similarity)

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
        product = pre_process(row["Product Name"])

        product_score = 0
        likely_product = ""
        if product in products:
            product_score = 1
            likely_product = product
        else:
            likely_product, product_score = closest(product, products, similarity)

        return {"likely_product": likely_product, "product_score": product_score}

    def get_numeric_score(self, key, row_key):
        row = self.row
        brand_data = self.brand_data
        likely_brand = self.likely_brand
        if row is None or brand_data is None or likely_brand is None:
            return {}

        val = closest_number(row[row_key])
        val_range = brand_data[likely_brand][key]
        val_score = std_similarity(val, val_range)

        return {
            f"{key}_score": val_score,
            f"likely_{key}": val,
            f"{key}_range": val_range,
        }

    def get_mrp_score(self):
        return self.get_numeric_score("mrp", "MRP")

    def get_net_weight_score(self):
        return self.get_numeric_score("net_weight", "Net Weight")

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

    def __call__(self, row):
        """
        Currently Uses:
            Brand Name
            Product Name
            MRP
            Net Weight
        """
        self.likely_brand = None
        self.row = row

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
