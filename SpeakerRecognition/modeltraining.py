import cPickle
import os
import numpy as np
from scipy.io.wavfile import read
from sklearn.mixture import GMM 
from featureextraction import extract_features
#from speakerfeatures import extract_features
import warnings
warnings.filterwarnings("ignore")
def ModelTraining(source = "trainingData/", dest = "Speakers_models/"):
    '''
        Trains model for Speaker recognition
        source => path to training data
        dest => path where training speakers will be saved
        train_file => file containing list of files for training (relative to source)
        num_training_samples => number of data samples for each speaker
    '''
            
    #file_paths = open(train_file,'r')

    count = 1
    # Extracting features for each speaker (5 files per speakers)
    features = np.asarray(())
    #Extacting featues for all speakers
    total_features = np.asarray(())
    spk_start = []
    spk_end = []
    model_names = []
    
    for speaker in os.listdir(source):
        path = os.path.join(source, speaker)
        print speaker
        if os.path.isdir(path):
            for filename in os.listdir(path):
                if filename.endswith(".wav"):
                    print filename
                    # read the audio
                    sr,audio = read(os.path.join(path, filename))
                    
                    # extract 40 dimensional MFCC & delta MFCC features
                    vector   = extract_features(audio,sr)
                    
                    if features.size == 0:
                        features = vector
                        spk_start.append(len(total_features))
                    else:
                        features = np.vstack((features, vector))   

                    # for UBM
                    if total_features.size == 0:
                        total_features = vector
                    else:
                        total_features = np.vstack((total_features, vector))                 
                    
            
            gmm = GMM(n_components = 16, n_iter = 200, covariance_type='diag',n_init = 3)
            gmm.fit(features)
            spk_end.append(len(total_features))
            # dumping the trained gaussian model
            model_names.append(speaker)
            picklefile = speaker +".gmm"
            cPickle.dump(gmm,open(dest + picklefile,'w'))
            print '+ modeling completed for speaker:',picklefile," with data point = ",features.shape   
            features = np.asarray(())
    # UBM Training
    for i in range(len(spk_start)):
        ubm = GMM(n_components = 16, n_iter = 200, covariance_type='diag',n_init = 3)
        ubm.fit(np.concatenate((total_features[:spk_start[i]], total_features[spk_end[i]:])))
        picklefile = model_names[i] +".ubm"
        cPickle.dump(ubm, open(dest + picklefile,'w'))
        print '+ UBM modeling completed for speaker:',picklefile


if __name__ == "__main__":
    ModelTraining()
