# -*- coding: utf-8 -*-
"""
Created on Tue Dec 31 19:56:30 2019

@author: darp_lord
"""

import numpy as np
import pandas as pd
from keras.layers import Dropout
from keras.layers import Dense
from keras.optimizers import Adam
from keras.models import Model
from keras_preprocessing.image import ImageDataGenerator

from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report
import keras.applications


DATA_DIR="../Datasets/HAM10000_images"

def append_ext(fn):
	return fn+".jpg"

metadata=pd.read_csv("../Datasets/HAM10000_metadata.csv", header=[0], index_col=[0])
metadata['image_id']=metadata['image_id'].apply(append_ext)


num_rows=224
num_cols=224
batch_size = 128
nb_epoch = 30
num_classes = 7
class_weights=compute_class_weight('balanced',
									 np.unique(metadata['dx']),
									 metadata['dx'].values)

train_datagen=ImageDataGenerator(
	rotation_range=180,
	rescale=1./255,
	width_shift_range=0.15,
	height_shift_range=0.15,
	horizontal_flip= True,
	vertical_flip=True,
	validation_split=0.2)

valid_datagen=ImageDataGenerator(rescale=1./255, validation_split=0.2)

train_generator=train_datagen.flow_from_dataframe(
											dataframe=metadata,
											directory=DATA_DIR,
											x_col="image_id",
											y_col="dx",
											subset="training",
											batch_size=batch_size,
											seed=169,
											shuffle=True,
											class_mode="categorical",
											target_size=(num_rows,num_cols))

valid_generator=train_datagen.flow_from_dataframe(
											dataframe=metadata,
											directory=DATA_DIR,
											x_col="image_id",
											y_col="dx",
											subset="validation",
											batch_size=batch_size,
											seed=169,
											shuffle=True,
											class_mode="categorical",
											target_size=(num_rows,num_cols))


mobile = keras.applications.mobilenet.MobileNet()

print(mobile.summary())

x = mobile.layers[-6].output

x = Dropout(0.25)(x)
predictions = Dense(7, activation='softmax')(x)

model = Model(inputs=mobile.input, outputs=predictions)

for layer in model.layers[:-23]:
	layer.trainable = False
model.compile(Adam(lr=0.01),loss="categorical_crossentropy",metrics=['accuracy','categorical_accuracy'])

STEP_SIZE_TRAIN=train_generator.n//train_generator.batch_size
STEP_SIZE_VALID=valid_generator.n//valid_generator.batch_size

model.fit_generator(generator=train_generator,
                    steps_per_epoch=STEP_SIZE_TRAIN*1.5,
                    validation_data=valid_generator,
                    validation_steps=STEP_SIZE_VALID,
                    epochs=nb_epoch,
					class_weight=class_weights,
					verbose=1
)

print(model.evaluate_generator(generator=valid_generator,steps=STEP_SIZE_VALID))
model.save("MobileNet.h5")

predictions=model.predict_generator(valid_generator,
									steps=STEP_SIZE_VALID,
									verbose=1)

print(classification_report(valid_generator.classes, np.argmax(predictions,axis=1), target_names=np.unique(metadata['dx'])))
