from sklearn.model_selection import train_test_split
import numpy as np
from tensorflow import keras
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder



def train_model(X, y):
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    X_train, _, y_train, _ = train_test_split(X, y_encoded, test_size=0.1)

    tokenizer = keras.layers.TextVectorization()
    tokenizer.adapt(X_train)
    X_train_tokenized = tokenizer(X_train)

    model = keras.Sequential([
        keras.layers.Embedding(input_dim=len(tokenizer.get_vocabulary()), output_dim=64),
        keras.layers.GlobalAveragePooling1D(),
        keras.layers.Dense(128, activation='relu'),
        keras.layers.Dense(len(label_encoder.classes_), activation='softmax')
    ])

    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    model.fit(X_train_tokenized, y_train, epochs=10, batch_size=32, validation_split=0.2)
    model.save("model.h5")


def get_form_field_type(form_field):
    model = tf.keras.models.load_model('model.h5')
    tokenizer = keras.layers.TextVectorization()
    label_encoder = LabelEncoder()
    
    new_inputs_tokenized = tokenizer(form_field)
    predictions = model.predict(new_inputs_tokenized)
    return label_encoder.inverse_transform(np.argmax(predictions, axis=1))

