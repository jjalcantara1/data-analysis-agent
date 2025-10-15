import json
import pandas as pd
import numpy as np

def numpy_encoder(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, pd.Series) or isinstance(obj, pd.Index):
        return obj.tolist()
    return json.JSONEncoder.default(obj)
