import pandas as pd
import numpy as np
import joblib
import json
import os

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score

data = pd.read_csv("dataset/winequality-white.csv",sep=";")
X = data.drop(['quality'],axis=1)
y = data['quality']

X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2, random_state=1234)

model = LinearRegression()
model.fit(X_train,y_train)

pred = model.predict(X_test)

accuracy = accuracy_score(pred,y_test)

print("Accuracy: ",accuracy)

os.makedirs("output", exist_ok=True)
joblib.dump(model,"output/model.pkl")
metrics = {
    "Accuracy: ",accuracy
}

with open("output/metrics.json","w") as file:
    json.dump(metrics,file)