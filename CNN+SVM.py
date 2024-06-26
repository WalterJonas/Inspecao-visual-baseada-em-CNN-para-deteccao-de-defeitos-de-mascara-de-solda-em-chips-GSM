import numpy as np
from os import listdir
from os.path import isfile, join
import cv2
import matplotlib.pyplot as plt
from sklearn.model_selection import KFold
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Flatten
from tensorflow.keras.optimizers import SGD
from sklearn.svm import SVC

class Provir3(object):
    
    def __init__(self):
        self.path1 = '/home/jonas/Walter - ICET/Dataset/'  #Modifique o diretório com base nas pastas do seu projeto
        self.X_train = []
        self.Y_train = []
        self.X_test = []
        self.Y_test = []

    def loadDataset(self, path, X_train, Y_train):
        self.files = [f for f in listdir(path) if isfile(join(path, f))]
        self.files.sort()

        print("Carregando dataset...")
        for i in range(len(self.files)):
            img = cv2.imread(join(path, self.files[i]), 1)
            img = cv2.resize(img, (0, 0), fx=0.2, fy=0.2)
            X_train.append(img)

            name = self.files[i].split("_")
            name = name[1].split(".")
            print (self.files[i].split("_"))
            if name[0] == '0':
                Y_train.append(0)
            elif name[0] == '1':
                Y_train.append(1)

        X_train = np.array(X_train)
        Y_train = np.array(Y_train)

        self.lin = img.shape[0]
        self.col = img.shape[1]

        X_train = X_train.reshape((X_train.shape[0], self.lin, self.col, 3))

        Y_train = to_categorical(Y_train)

        X_train = X_train.astype('float32')
        X_train = X_train / 255.0

        return X_train, Y_train

    def define_model(self):
        model = Sequential()
        model.add(Conv2D(32, (7, 7), activation='relu', kernel_initializer='he_uniform', input_shape=(self.lin, self.col, 3)))
        model.add(MaxPooling2D((2, 2)))
        model.add(Conv2D(32, (7, 7), activation='relu', kernel_initializer='he_uniform'))
        model.add(MaxPooling2D((2, 2)))
        model.add(Conv2D(64, (5, 5), activation='relu', kernel_initializer='he_uniform'))
        model.add(MaxPooling2D((2, 2)))
        
        model.add(Flatten())
        model.add(Dense(100, activation='relu', kernel_initializer='he_uniform'))
        model.add(Dense(2, activation='softmax'))
        opt = SGD(learning_rate=0.001, momentum=0.9)
        model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])
        return model

    def evaluate_model(self, dataX, dataY, tstX, tstY, n_folds=5):
        print("Avaliando modelo...")
        scores, histories, svm_accuracies = [], [], []
        kfold = KFold(n_folds, shuffle=True, random_state=1)
        for train_ix, test_ix in kfold.split(dataX):
            if len(train_ix) == 0 or len(test_ix) == 0:
                print("Conjunto de treinamento ou teste vazio. Pulando esta divisão.")
                continue
            model = self.define_model()
            trainX, trainY, testX, testY = dataX[train_ix], dataY[train_ix], dataX[test_ix], dataY[test_ix]
            history = model.fit(trainX, trainY, epochs=40, batch_size=32, validation_data=(testX, testY), verbose=1)
            _, acc = model.evaluate(testX, testY, verbose=1)
            print('> CNN Accuracy: %.3f' % (acc * 100.0))
            scores.append(acc)
            histories.append(history)

            # Extração de características das camadas
            feature_extractor = Sequential(model.layers[:-2])
            features_train = feature_extractor.predict(trainX)
            features_test = feature_extractor.predict(testX)

            # Treinamento e avaliação da SVM
            svm_classifier = SVC(kernel='linear')
            svm_classifier.fit(features_train, np.argmax(trainY, axis=1))
            svm_accuracy = svm_classifier.score(features_test, np.argmax(testY, axis=1))
            print('> SVM Accuracy: %.3f' % (svm_accuracy * 100.0))
            svm_accuracies.append(svm_accuracy)

        return scores, histories, svm_accuracies

    def summarize_performance(self, scores, svm_accuracies):
        print('CNN Accuracy: mean=%.3f std=%.3f, n=%d' % (np.mean(scores) * 100, np.std(scores) * 100, len(scores)))
        print('SVM Accuracy: mean=%.3f std=%.3f, n=%d' % (np.mean(svm_accuracies) * 100, np.std(svm_accuracies) * 100, len(svm_accuracies)))

    def summarize_diagnostics(self, histories):
        for i in range(len(histories)):
            plt.subplot(2, 1, 1)
            plt.title('Cross Entropy Loss')
            plt.plot(histories[i].history['loss'], color='blue', label='train')
            plt.plot(histories[i].history['val_loss'], color='orange', label='test')
            plt.subplot(2, 1, 2)
            plt.title('Classification Accuracy')
            plt.plot(histories[i].history['accuracy'], color='blue', label='train')
            plt.plot(histories[i].history['val_accuracy'], color='orange', label='test')
        plt.show()

if __name__ == '__main__':
    obj = Provir3()

    #-------------LOAD IMAGES--------------------
    print("-------------LOAD IMAGES--------------------")
    obj.X_train, obj.Y_train = obj.loadDataset(obj.path1, obj.X_train, obj.Y_train)
    print(obj.X_train.shape)
    print(obj.Y_train.shape)

    #-------------CNN MODEL SETTING--------------------
    # obj.define_model()

    #-------------CNN FITTING--------------------
    scores, histories, svm_accuracies = obj.evaluate_model(obj.X_train, obj.Y_train, obj.X_test, obj.Y_test)

    #-------------ACCURACY COMPUTING--------------------
    obj.summarize_performance(scores, svm_accuracies)

    #-------------PLOT LOSS AND ACCURACY--------------------
    #obj.summarize_diagnostics(histories)

