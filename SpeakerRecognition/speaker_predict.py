import os
import cPickle
import numpy as np
from scipy.io.wavfile import read
from featureextraction import extract_features
#from speakerfeatures import extract_features
import warnings
warnings.filterwarnings("ignore")

class GMM_UBM():
    '''
    Class for loading speaker models and predicting speaker
    '''
    def __init__(self):
        '''
        Initalises variables
        '''
        self.gmm_files = []
        self.ubm_files = []
                  
        self.gmm_models    = []
        self.ubm_models    = []
        self.speakers   = []
        
    def load_models(self, modelpath = "Speakers_models/"):
        """ Load Models from file"""
        self.gmm_files = [os.path.join(modelpath,fname) for fname in 
                  os.listdir(modelpath) if fname.endswith('.gmm')]
        self.ubm_files = [os.path.join(modelpath,fname) for fname in 
                  os.listdir(modelpath) if fname.endswith('.ubm')]
                  
        self.gmm_models    = [cPickle.load(open(fname,'r')) for fname in self.gmm_files]
        self.ubm_models    = [cPickle.load(open(fname,'r')) for fname in self.ubm_files]
        self.speakers   = [fname.split("/")[-1].split(".gmm")[0] for fname in self.gmm_files]
        
    def predict_speaker(self, audio, sr):
        '''
        Predicts the speaker to which audio belog to.
        returns 2-tuple 
            in-set-speaker => boolean
            predicted speaker => string 
        '''
        vector   = extract_features(audio,sr)
        gmm_log_likelihood = np.zeros(len(self.gmm_models))
        ubm_log_likelihood = np.zeros(len(self.ubm_models))
        for i in range(len(self.gmm_models)):
		    gmm    = self.gmm_models[i]  #checking with each model one by one
		    scores = np.array(gmm.score(vector))
		    gmm_log_likelihood[i] = scores.sum()
		    ubm    = self.ubm_models[i]  #checking with each model one by one
		    scores = np.array(ubm.score(vector))
		    ubm_log_likelihood[i] = scores.sum()
        winner = np.argmax(gmm_log_likelihood)
       
        if gmm_log_likelihood[winner] - ubm_log_likelihood[winner] > 0:
            return (True, self.speakers[winner])
        else:
            return (False, self.speakers[winner])

if __name__ == "__main__":
    test_file = "testSamplePath.txt"
    source   = "SampleData/"
    modelpath = "Speakers_models/"
    predict_spk = GMM_UBM()
    predict_spk.load_models(modelpath)
    for speaker in os.listdir(source):
        path = os.path.join(source, speaker)
        if os.path.isdir(path):
            for filename in os.listdir(path):
                if filename.endswith(".wav"):
                    #print "Testing Audio : ", os.path.join(path, filename)
                    sr,audio = read(os.path.join(path, filename))
                    print speaker, predict_spk.predict_speaker(audio, sr)
	            
