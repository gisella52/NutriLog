# -*- coding: utf-8 -*-
"""Abon haruwan

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1kc6aHA9U74FCx_vBNF-qjqwPFpXLGCCl
"""

import os
import tensorflow as tf
import numpy as np
import pandas as pd
from tensorflow.keras.layers import Input
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from sklearn.model_selection import train_test_split
import requests
from PIL import Image
from io import BytesIO
from sklearn.preprocessing import StandardScaler

# Load the dataset
data = pd.read_csv('nutrition.csv')

# Display the first few rows of the dataset
print(data.head())

# Check the dataset's info
print(data.info())

# Summary statistics
print(data.describe())

# Check for missing values
print(data.isnull().sum())

# Drop rows with missing values (if any)
data = data.dropna()

# Normalize the nutritional data (calories, fat, protein, carbohydrate)
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
data[['calories', 'fat', 'proteins', 'carbohydrate']] = scaler.fit_transform(data[['calories', 'fat', 'proteins', 'carbohydrate']])

# Function to load and preprocess images from URLs with headers
def load_and_preprocess_image_from_url(url, food_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        img = Image.open(BytesIO(response.content))
        img = img.resize((224, 224))  # Resize images to 224x224
        img_array = np.array(img.convert('L'))  # Convert to grayscale
        img_array = img_array / 255.0  # Normalize pixel values to [0, 1]
        return food_name, img_array
    except Exception as e:
        print(f"Error processing image at URL {url}: {e}")
        return None, None

# Apply the function to the image paths in the dataset
data['food_name'], data['image_data'] = zip(*data.apply(lambda row: load_and_preprocess_image_from_url(row['image'], row['name']), axis=1))

# Filter out rows where image_data is not of shape (224, 224)
filtered_data = data[data['image_data'].apply(lambda x: x is not None and x.shape == (224, 224))]

# Convert image data and labels to numpy arrays
X = np.array(filtered_data['image_data'].tolist())
y = filtered_data[['calories', 'fat', 'proteins', 'carbohydrate']].values

# Reshape X to add the channel dimension (grayscale)
X = X.reshape(-1, 224, 224, 1)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test, food_name_train, food_name_test = train_test_split(X, y, filtered_data['food_name'].tolist(), test_size=0.2, random_state=42)

from tensorflow.keras.layers import Dropout
# Define the model with an explicit InputLayer
input_layer = Input(shape=(224, 224, 1), name='input_layer')
x = Conv2D(32, (3, 3), activation='relu')(input_layer)
x = MaxPooling2D((2, 2))(x)
x = Dropout(0.25)(x)
x = Conv2D(64, (3, 3), activation='relu')(x)
x = MaxPooling2D((2, 2))(x)
x = Dropout(0.25)(x)
x = Flatten()(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.5)(x)
output_layer = Dense(4)(x)

model = tf.keras.models.Model(inputs=input_layer, outputs=output_layer)

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])

# Train the model
history = model.fit(X_train, y_train, epochs=20, validation_split=0.2)

# Evaluate the model on the test set
test_loss, test_mae = model.evaluate(X_test, y_test)
print(f'Test MAE: {test_mae}')

# Save the model
model.save('nutrition_model.h5')

import tensorflow as tf

# Load the trained model
model = tf.keras.models.load_model('nutrition_model.h5')

# Convert the model to TensorFlow Lite format with quantization
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

# Save the .tflite model
with open('nutrition_model_pruned_quantized.tflite', 'wb') as f:
    f.write(tflite_model)

print('Model has been successfully converted to .tflite format and saved.')

import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler
import joblib

# Load the dataset
data = pd.read_csv('nutrition.csv')

# Drop rows with missing values (if any)
data = data.dropna()

# Normalize the nutritional data (calories, fat, proteins, carbohydrate)
scaler = StandardScaler()
data[['calories', 'fat', 'proteins', 'carbohydrate']] = scaler.fit_transform(data[['calories', 'fat', 'proteins', 'carbohydrate']])

# Create and fit the LabelEncoder
label_encoder = LabelEncoder()
data['encoded_name'] = label_encoder.fit_transform(data['name'])

# Save the LabelEncoder
joblib.dump(label_encoder, 'label_encoder.save')
joblib.dump(scaler, 'scaler.save')

# Load the dataset
data = pd.read_csv('nutrition.csv')

# Drop rows with missing values (if any)
data = data.dropna()

# Load the saved scaler
scaler = joblib.load('scaler.save')

# Function to load and preprocess images from URLs with headers
def load_and_preprocess_image_from_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        img = Image.open(BytesIO(response.content))
        img = img.resize((224, 224))  # Resize images to 224x224
        img_array = np.array(img.convert('L'))  # Convert to grayscale
        img_array = img_array / 255.0  # Normalize pixel values to [0, 1]
        return img_array
    except Exception as e:
        print(f"Error processing image at URL {url}: {e}")
        return None

# Function to predict food item from image URL
def predict_food_item(image_url):
    image_data = load_and_preprocess_image_from_url(image_url)

    if image_data is not None:
        # Reshape image data to match input shape
        input_data = np.expand_dims(image_data, axis=0).astype(np.float32)
        input_data = np.expand_dims(input_data, axis=-1)

        # Load the trained model
        model = tf.keras.models.load_model('nutrition_model.h5')

        # Predict the food item
        prediction = model.predict(input_data)
        predicted_label = np.argmax(prediction, axis=1)
        food_item = label_encoder.inverse_transform(predicted_label)[0]

        return food_item
    else:
        return None

# Function to fetch nutritional information
def fetch_nutrition_info(food_item):
    food_data = data[data['name'] == food_item].iloc[0]
    return {
        'food_name': food_data['name'],
        'calories': food_data['calories'],
        'fat': food_data['fat'],
        'proteins': food_data['proteins'],
        'carbohydrate': food_data['carbohydrate']
    }

# Example usage
image_url = 'https://asset.kompas.com/crops/smfd25xgXRE3HpMLb2aamPeulYM=/21x0:1476x970/1200x800/data/photo/2022/08/30/630d7ae5d041f.jpg'
predicted_food_item = predict_food_item(image_url)

if predicted_food_item:
    nutrition_info = fetch_nutrition_info(predicted_food_item)
    print(f"Food: {nutrition_info['food_name']}")
    print(f"Calories: {nutrition_info['calories']}")
    print(f"Fat: {nutrition_info['fat']}")
    print(f"Proteins: {nutrition_info['proteins']}")
    print(f"Carbohydrate: {nutrition_info['carbohydrate']}")
else:
    print("Could not predict food item from the provided image.")