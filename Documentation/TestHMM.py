import os, sys
from python_speech_features import mfcc
from python_speech_features import logfbank
import scipy.io.wavfile as wav
import numpy as np
from hmmlearn import hmm


all_features = None
lengths = []
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "enter filename for processing as the argument"
    else:
        i = True
        directory = sys.argv[1]
        for filename in os.listdir(directory):
            if filename.endswith(".wav"): 
                print(os.path.join(directory, filename))
                (rate, sig) = wav.read(os.path.join(directory, filename))
                print rate
                mfcc_features = mfcc(sig, rate, numcep=16)
                lengths.append(len(mfcc_features))
                if i:
                    all_features = mfcc_features
                    i = False
                else:
                    all_features = np.append(all_features, mfcc_features, axis=0)
                print len(all_features), len(mfcc_features)
        remodel = hmm.GaussianHMM(n_components=16, n_iter=1000)
        #print all_features
        print lengths
        remodel.fit(all_features, lengths)
        lengths = []
        all_features = []
        i = True
        directory = "SpeechRecognition/TrainingData/Silence/"
        for filename in os.listdir(directory):
            if filename.endswith(".wav"): 
                print(os.path.join(directory, filename))
                (rate, sig) = wav.read(os.path.join(directory, filename))
                print rate
                mfcc_features = mfcc(sig, rate, numcep=16)
                lengths.append(len(mfcc_features))
                if i:
                    all_features = mfcc_features
                    i = False
                else:
                    all_features = np.append(all_features, mfcc_features, axis=0)
                print len(all_features), len(mfcc_features)
        print all_features
        silencemodel = hmm.GaussianHMM(n_components=16, n_iter=1000)
        silencemodel.fit(all_features, lengths)
        cla = []
        for filename in os.listdir("SpeechRecognition/TrainingData/Open/"):
            if filename.endswith(".wav"): 
                print(os.path.join("SpeechRecognition/TrainingData/Open/", filename))
                (rate, sig) = wav.read(os.path.join("SpeechRecognition/TrainingData/Open/", filename))
                print rate
                mfcc_features = mfcc(sig, rate, numcep=16)
                X = mfcc_features
                ret = remodel.predict(mfcc_features)
                print os.path.join(directory, filename)
                open_llh = remodel.decode(X, algorithm='viterbi')[0]
                print open_llh
                silence_llh = silencemodel.decode(X, algorithm='viterbi')[0]
                print silence_llh
                if open_llh > silence_llh:
                    cla.append(1)
                else:
                    cla.append(0)
        for filename in os.listdir("SpeechRecognition/TrainingData/Silence/"):
            if filename.endswith(".wav"): 
                print(os.path.join("SpeechRecognition/TrainingData/Silence/", filename))
                (rate, sig) = wav.read(os.path.join("SpeechRecognition/TrainingData/Silence/", filename))
                print rate
                mfcc_features = mfcc(sig, rate, numcep=16)
                X = mfcc_features
                ret = remodel.predict(mfcc_features)
                print os.path.join(directory, filename)
                # print ret
                open_llh = remodel.decode(X, algorithm='viterbi')[0]
                print open_llh
                silence_llh = silencemodel.decode(X, algorithm='viterbi')[0]
                print silence_llh
                if open_llh > silence_llh:
                    cla.append(0)
                else:
                    cla.append(1)
                # print remodel.predict_proba(mfcc_features)
                # print remodel._compute_log_likelihood(X)
                # print list(set(ret))
                
        print "Start Prob"
        print remodel.startprob_
        print sum(remodel.startprob_)
        print "transmat"
        print remodel.transmat_
        print cla
            
