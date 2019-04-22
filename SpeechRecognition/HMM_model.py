import os, sys
import cPickle
from python_speech_features import mfcc
from scipy.io.wavfile import read
import numpy as np
from hmmlearn import hmm
import warnings
warnings.filterwarnings("ignore")

class SpeechRecognizer():
    '''
    Trains and loads speech models and predit the speech
    '''
    def __init__(self):
        '''
        Initalizes the variables
        '''
        self.hmm_files = []
        self.hmm_models = []
        self.speech = []
        
    def load_models(self, modelpath = "Speech_Models/"):
        '''
        loads all models in given path
        '''
        self.hmm_files = [os.path.join(modelpath,fname) for fname in 
                           os.listdir(modelpath) if fname.endswith('.hmm')]
        self.speech    = [fname.split("/")[-1].split(".hmm")[0] for fname in self.hmm_files]
        self.hmm_models    = [cPickle.load(open(fname,'r')) for fname in self.hmm_files]
        
    def train_hmm(self, source = "TrainingData/", dest = "Speech_Models/", train_file = "TrainingData.txt"):
        '''
        trains the model and saves it in dest
        trainfile contains the foldername for which we need to train (relative to source folder).
        '''
        with open(train_file,'r') as source_folders:
            for speech in source_folders:
                speech_folder = speech.strip()
                directory = source + speech_folder + "/"
                lengths = []
                features = np.asarray(())
                for filename in os.listdir(directory):
                    if filename.endswith(".wav"):
                        file_path = os.path.join(directory, filename)
                        (rate, sig) = read(file_path)
                        # feature extraction
                        mfcc_features = mfcc(sig, rate, numcep=16)
                        lengths.append(len(mfcc_features))
                        
                        if features.size == 0:
                            features = mfcc_features
                        else:
                            features = np.append(features, mfcc_features, axis=0)
                model = hmm.GaussianHMM(n_components=16, n_iter=1000)
                model.fit(features, lengths)
                picklefile = speech_folder +".hmm"
                cPickle.dump(model, open(dest + picklefile,'w'))
                print '+ HMM modeling completed for speech:', picklefile

    def predit_speech(self, audio, sr):
        '''
        predits the speech given by audio.
        '''
        mfcc_features = mfcc(audio, sr, numcep=16)
        log_likelihood = np.zeros(len(self.hmm_models))
        for i in range(len(self.hmm_models)):
            score = self.hmm_models[i].score(mfcc_features)
            log_likelihood[i] = score
        winner = np.argmax(log_likelihood)
        return self.speech[winner]
                           
        
if __name__ == "__main__":
    modelpath = "Speech_Models/"
    sph_rec = SpeechRecognizer()
    #sph_rec.train_hmm(source = "TrainingData/", dest = "Speech_Models/" , train_file = "TrainingData.txt")
    test_file = "TestingDataPath.txt"
    file_paths = open(test_file,'r')
    sph_rec.load_models(modelpath)
    test_source = "TestingData/"
    for filename in os.listdir(test_source):
        if filename.endswith(".wav"):
            print "Testing Audio : ", os.path.join(test_source, filename)
            sr,audio = read(os.path.join(test_source, filename))
            predicted_speech = sph_rec.predit_speech(audio, sr)
            print "+ speech predicted as ",  predicted_speech
    file_paths.close()
