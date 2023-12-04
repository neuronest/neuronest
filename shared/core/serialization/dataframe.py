import base64
import pickle

import numpy as np
import pandas as pd


def dataframe_to_string(dataframe: pd.DataFrame, encoding: str = "utf-8") -> str:
    return base64.b64encode(pickle.dumps(dataframe)).decode(encoding)


def dataframe_from_string(
    encoded_dataframe: str, encoding: str = "utf-8"
) -> np.ndarray:
    return pickle.loads(base64.b64decode(encoded_dataframe.encode(encoding)))
