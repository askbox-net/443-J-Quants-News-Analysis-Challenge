# -*- coding:utf-8 -*-

import pandas as pd
import numpy as np
import predictor

dataset_dir = '../../data'

inputs = {
    "stock_list": f"{dataset_dir}/stock_list.csv",
    "stock_price": f"{dataset_dir}/stock_price.csv",
    "stock_fin": f"{dataset_dir}/stock_fin.csv",
    "stock_fin_price": f"{dataset_dir}/stock_fin_price.csv",
    "stock_labels": f"{dataset_dir}/stock_labels.csv",
}

start_dt=pd.Timestamp("2020-12-01")
p = predictor.ScoringService.predict(inputs, start_dt)
print(p)
