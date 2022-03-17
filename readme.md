# Anomaly detection

## Usage

### Train

1. To use the model, simply import the `Scorer` class from `scorer.py`
1. The model is an instance of the `Scorer` class. The constructor does not take any arguments.
1. Before being used, the model needs to be trained on some valid data:

#### Example

```
from scorer import Scorer
import pandas as pd

df = pd.read_csv("./data/train-modified.csv", dtype={"Fssai Lic. No.": str})

scorer = Scorer()
scorer.train(df)
```

_Note_: The model needs a pandas dataframe of some valid data. It uses this data to extract likely brand names, product names, mrp, weight ratio etc for new inputs passed. An example of valid data can be found in `/data/train-modified.csv`

### Test

To use the model to generate likelihood scores, just call the model like a function.
_Note_: The function expects 1 required parameter - the input. The input needs to be an indexable dict-like
object (like a dict, pandas dataframe row etc.) with the following `str` type keys:

```
"Product Name"
"Manufacturer Name" (optional)
"Product GTIN"
"MRP"
"Net Weight"
"Fssai Lic. No."
"Consumer Care Email"
```

#### Examples

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
