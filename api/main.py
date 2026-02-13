from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import joblib

app = FastAPI()
model = joblib.load("model.pkl")

class WineInput(BaseModel):
    fixed_acidity: float
    volatile_acidity: float
    citric_acid: float
    residual_sugar: float
    chlorides: float
    free_sulfur_dioxide: float
    total_sulfur_dioxide: float
    density: float
    pH: float
    sulphates: float
    alcohol: float

@app.post("/predict",)
def predict(request: WineInput):
    inp = np.array([[
        request.fixed_acidity,
        request.volatile_acidity,
        request.citric_acid,
        request.residual_sugar,
        request.chlorides,
        request.free_sulfur_dioxide,
        request.total_sulfur_dioxide,
        request.density,
        request.pH,
        request.sulphates,
        request.alcohol
    ]])
    prediction = model.predict(inp)

    return {
        "name":"Arjun Sreenivas",
        "roll_no": "2022BCS0060",
        "wine_quality": float(prediction[0])
    }