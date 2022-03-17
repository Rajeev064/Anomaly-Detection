# Anomaly detection

## Usage:

### Train

1. scorer.py is the only relvant file to import and use
2. Before begin used, the model needs to be trained on some valid data:

```
from scorer import Scorer
import pandas as pd

df = pd.read_csv("./data/train-modified.csv", dtype={"Fssai Lic. No.": str})

scorer = Scorer()
scorer.train(df)
```

_Note_: The model needs a pandas dataframe of some valid data. It uses this data to extract likely brand names, product names, mrp, weight ratio etc for new inputs passed

### Test

To use the model to generate likelihood scores, just call the model like a function:

```
print(
    scorer(df.iloc[0])
)
```

_OR_

```
print(
    scorer({
        "Manufacturer Name": "KELLOG INDIA PVT. LTD",
        "Product Name": "Corn Flakes",
        "Product GTIN": "8901499009661",
        "MRP": 99,
        "Net Weight": 290,
        "Fssai Lic. No.": "10013022002031",
        "Consumer Care Email": "kconsumer@kellogg.com"
    })
)
```

_Note_: The model only input needs to be indexable dict-like object (like a dict, pandas dataframe row etc.) with the following _string_ keys:

```
    "Product Name"
    "Manufacturer Name" (optional)
    "Product GTIN"
    "MRP"
    "Net Weight"
    "Fssai Lic. No."
    "Consumer Care Email"
```
