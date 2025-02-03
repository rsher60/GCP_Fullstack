from fastapi import FastAPI, Depends, Body
import pandas as pd
import numpy as np
import uvicorn
from google.cloud import aiplatform
import os


app = FastAPI()
#added code
@app.get('/predict')
#instances will be an input but hardcoding for now.
def endpoint_predict_sample(
  ):
    aiplatform.init(project='1031406148701', location='us-central1')

    endpoint = aiplatform.Endpoint("8496560766034378752")
    instances = [[23.0,
                 12.0,
                 19114.12,
                 3.0,
                 4.0,
                 3.0,
                 4.0,
                 6.0,
                 11.27,
                 4.0,
                 1.0,
                 809.98,
                 24.797346908844982,
                 186.0,
                 1.0,
                 49.57494921489417,
                 1.0,
                 341.48923103222177]]
    prediction = endpoint.predict(instances=instances)
    #print(prediction)
    return {"data": prediction}

