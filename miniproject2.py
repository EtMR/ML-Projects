# -*- coding: utf-8 -*-
"""Miniproject2

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/13FOUSwGfasOWw6XYo4ZV_L3nqvfPn7vv
"""

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from random import randint

from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score, KFold 

from keras.models import Model
from keras.models import Sequential

from keras.utils.np_utils import to_categorical
from keras.layers import Input, Dense, Activation, ZeroPadding2D, BatchNormalization, Flatten, Conv2D
from keras.layers import AveragePooling2D, MaxPooling2D, Dropout, GlobalMaxPooling2D, GlobalAveragePooling2D

from google.colab import drive
drive.mount('/content/gdrive')

# Import data and turned them into numpy format
# Study the shape of the data
train_images = pd.read_pickle('/content/gdrive/My Drive/Colab Notebooks/[CS 230]/Miniproject2/input/train_images.pkl/train_images.pkl')
train_labels = pd.read_csv('/content/gdrive/My Drive/Colab Notebooks/[CS 230]/Miniproject2/input/train_labels.csv')
train_labels = train_labels.to_numpy()
test_images = pd.read_pickle('/content/gdrive/My Drive/Colab Notebooks/[CS 230]/Miniproject2/input/test_images.pkl/test_images.pkl')

print('train_images: ', train_images.shape, type(train_images))
print('train_labels: ', train_labels.shape, type(train_labels))
print('test_images: ', test_images.shape, type(test_images))

# Encode Y-train into 10 class matrix
# Study some of the cases
Y_train = to_categorical(train_labels[:, 1], num_classes = 10)
print('Convert Y_train into 10-dims matrix: ', Y_train.shape)

check1 = randint(0, 40000)
check2 = randint(0, 40000)
print('Random Y check (Y = ' + str(check1) + ') : ', train_labels[check1][1], Y_train[check1])
plt.imshow(train_images[check1])
plt.show()

print('Random Y check (Y = ' + str(check2) + ') : ', train_labels[check2][1], Y_train[check2])
plt.imshow(train_images[check2])
plt.show()

# Normalized data
print('Before Normalization (Y = ' + str(check1) + ') (Mean, Std): ', np.average(train_images[check1]), np.std(train_images[check1]))
train_images /= 255
test_images /= 255
print('After Normalization (Y = ' + str(check1) + ') (Mean, Std): ', np.average(train_images[check1]), np.std(train_images[check1]))

# Process data (1) get rid of noise, (2) find largest area number
# train_images:  (40000, 64, 64) <class 'numpy.ndarray'>
# train_labels:  (40000, 2) <class 'numpy.ndarray'>
# test_images:  (10000, 64, 64) <class 'numpy.ndarray'>

output = [0]*len(train_images)
for j in range(len(train_images)):
    img = train_images[j]  
    img = img.astype(np.uint8)
    (thresh, im_bw) = cv2.threshold(img, 0.7, 1, cv2.THRESH_BINARY)
    _, contours, _= cv2.findContours(im_bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    coord = (0,0,0,0)
    max_side = 0
    for cont in contours:
        x,y,w,h = cv2.boundingRect(cont)
        side = max(w,h)
        if side > max_side:
            coord = x,y,w,h
            max_side = side
    x,y,w,h = coord
    crop_img = im_bw[y+1:y+h, x+1:x+w]
    im = crop_img
    result = np.zeros((64,64))
    result[int((64-h)/2):int((64-h)/2)+im.shape[0],int((64-w)/2):int((64-w)/2)+im.shape[1]] = im   
    output[j] = result
X_train = np.array(np.float32(output))

print('Results after image processing')
print('X_train shape', X_train.shape)
plt.imshow(X_train[check1])
plt.show()

plt.imshow(X_train[check2])
plt.show()

def NumModel(input_shape):
    
    # Define the input placeholder as a tensor with shape input_shape. Think of this as your input image!
    X_input = Input(input_shape) # (64, 64, 1)

    # Zero-Padding: pads the border of X_input with zeroes
    X = ZeroPadding2D((3, 3))(X_input) # (70, 70, 1)

    # CONV -> BN -> RELU Block applied to X
    X = Conv2D(32, (7, 7), strides = (1, 1), name = 'conv0')(X) # (64, 64, 32)
    X = BatchNormalization(axis = 3, name = 'bn0')(X) # (64, 64, 32) Normalized over filters???
    X = Activation('relu')(X)

    # MAXPOOL
    X = MaxPooling2D((2, 2), name='max_pool0')(X) # (32, 32, 32)

    # Zero-Padding: pads the border of X_input with zeroes
    X = ZeroPadding2D((3, 3))(X) # (38, 38, 32)

    # CONV -> BN -> RELU Block applied to X
    X = Conv2D(64, (7, 7), strides = (1, 1), name = 'conv1')(X) # (32, 32, 64)
    X = BatchNormalization(axis = 3, name = 'bn1')(X) # (32, 32, 64) Normalized over filters???
    X = Activation('relu')(X)

    # MAXPOOL
    X = MaxPooling2D((2, 2), name='max_pool1')(X) # (16, 16, 64)

    
    # CONV -> BN -> RELU Block applied to X
    X = Conv2D(64, (1, 1), strides = (1, 1), name = 'conv2')(X) # (16, 16, 64)
    X = BatchNormalization(axis = 3, name = 'bn2')(X) # (16, 16, 64) Normalized over filters???
    X = Activation('relu')(X)
    
    
    # FLATTEN X (means convert it to a vector) + FULLYCONNECTED
    X = Flatten()(X) # (1, 16384)
    X = Dense(1280, input_shape=(16384,), activation='relu', name='fc0')(X)
    X = Dropout(0.5)(X)
    X = Dense(256, activation='relu', name='fc1')(X)
    X = Dropout(0.5)(X)
    X = Dense(10, activation='softmax', name='fc2')(X)

    # Create model. This creates your Keras model instance, you'll use this instance to train/test the model.
    model = Model(inputs = X_input, outputs = X, name='NumModel') 
      
    return model

X_train = X_train.reshape(-1, 64, 64, 1)

numModel = NumModel((64, 64, 1))

numModel.compile(loss='categorical_crossentropy', optimizer='adam', metrics = ["accuracy"])

history = numModel.fit(X_train, Y_train, validation_split=0.1, epochs=50, batch_size=64, verbose=1)

# Plot training & validation accuracy values
plt.plot(history.history['acc'])
plt.plot(history.history['val_acc'])
plt.title('Model accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Test'], loc='upper left')
plt.show()

# Plot training & validation loss values
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Test'], loc='upper left')
plt.show()