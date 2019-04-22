from __future__ import print_function
import wave
import ConfigParser
import pyaudio
import struct
import math
import numpy as np
from scipy import signal, stats
from vad import calculate_features_for_VAD, smooth_spoken_frames

FRAME_DURATION = 0.01
INIT_SILENCE_FRAMES = 30
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

class VoiceActivityDetection():
    def __init__(self, sampling_frequency = RATE, configfile = "Config/vad.cfg"):
        self.default_parms = {}
        self.read_config(configfile)
        self.stop_thread = False
        self.sampling_frequency = sampling_frequency
        [self.min_energy, self.min_sfm, self.min_freq] = [0,0,0]
        self.initalize_VAD_min()
        
    def initalize_VAD_min(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, 
                            channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)
        silence_frames = []
        for i in range(0, int(RATE / CHUNK * 1)):
            data = stream.read(CHUNK)
            silence_frames.append(data)
        sound_data = b''.join(silence_frames)
        assert self.sampling_frequency >= 8000, 'Sampling frequency is inadmissible!'
        n_data = len(sound_data)
        assert (n_data > 0) and ((n_data % 2) == 0), 'Sound data are wrong!'
        frame_size = int(round(FRAME_DURATION * float(self.sampling_frequency)))
        n_fft_points = 2
        while n_fft_points < frame_size:
            n_fft_points *= 2
        sound_signal = np.empty((int(n_data / 2),))
        for ind in range(sound_signal.shape[0]):
            sound_signal[ind] = float(struct.unpack('<h', sound_data[(ind * 2):(ind * 2 + 2)])[0])
        frequencies_axis, time_axis, spectrogram = signal.spectrogram(sound_signal,
                                                                      fs=self.sampling_frequency,
                                                                      window='hamming',
                                                                      nperseg=frame_size,
                                                                      noverlap=0,
                                                                      nfft=n_fft_points,
                                                                      scaling='spectrum',
                                                                      mode='psd')
        spectrogram = spectrogram.transpose()
        if (sound_signal.shape[0] % frame_size) == 0:
            sound_frames = np.reshape(sound_signal, (spectrogram.shape[0], frame_size))
        else:
            sound_frames = np.reshape(sound_signal[0:int(sound_signal.shape[0] / frame_size) *
                                                   frame_size], (spectrogram.shape[0], frame_size))
        features = calculate_features_for_VAD(sound_frames, frequencies_axis, spectrogram)
        del sound_frames
        del spectrogram
        del frequencies_axis
        del time_axis
        [self.min_energy, self.min_sfm, self.min_freq] = features[0:INIT_SILENCE_FRAMES].min(axis=0).tolist()
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
    def read_config(self, config_file):
        config = ConfigParser.RawConfigParser()
        config.read(config_file)
        self.default_parms['Energy_PrimThresh'] = config.getfloat('VAD', 'Energy_PrimThresh')
        self.default_parms['F_PrimThresh'] = config.getfloat('VAD', 'F_PrimThresh')
        self.default_parms['SF_PrimThresh'] = config.getfloat('VAD', 'SF_PrimThresh')
        self.default_parms['Min_Silence'] = config.getfloat('VAD', 'Min_Silence')
        self.default_parms['Min_Speech'] = config.getfloat('VAD', 'Min_Speech')
    
    def detect_spoken_frames(self, sound_data, sampling_frequency):
        '''        
        def on_button_click(self, widget):
            self.button_window = PreferencesWindow()
            self.button_window.show_all()
            #help(self   )
        '''
        assert sampling_frequency >= 8000, 'Sampling frequency is inadmissible!'
        n_data = len(sound_data)
        assert (n_data > 0) and ((n_data % 2) == 0), 'Sound data are wrong!'
        frame_size = int(round(FRAME_DURATION * float(sampling_frequency)))
        n_fft_points = 2
        while n_fft_points < frame_size:
            n_fft_points *= 2
        sound_signal = np.empty((int(n_data / 2),))
        for ind in range(sound_signal.shape[0]):
            sound_signal[ind] = float(struct.unpack('<h', sound_data[(ind * 2):(ind * 2 + 2)])[0])
        frequencies_axis, time_axis, spectrogram = signal.spectrogram(sound_signal,
                                                                      fs=sampling_frequency,
                                                                      window='hamming',
                                                                      nperseg=frame_size,
                                                                      noverlap=0,
                                                                      nfft=n_fft_points,
                                                                      scaling='spectrum',
                                                                      mode='psd')
        spectrogram = spectrogram.transpose()
        if spectrogram.shape[0] <= INIT_SILENCE_FRAMES:
            return []
        if (sound_signal.shape[0] % frame_size) == 0:
            sound_frames = np.reshape(sound_signal, (spectrogram.shape[0], frame_size))
        else:
            sound_frames = np.reshape(sound_signal[0:int(sound_signal.shape[0] / frame_size) *
                                                   frame_size], (spectrogram.shape[0], frame_size))
        features = calculate_features_for_VAD(sound_frames, frequencies_axis, spectrogram)
        #print (features)
        del sound_frames
        del spectrogram
        del frequencies_axis
        del time_axis
        #[min_energy, min_sfm, min_freq] = features[0:INIT_SILENCE_FRAMES].min(axis=0).tolist()
        energy_th = self.default_parms['Energy_PrimThresh'] * math.log(self.min_energy)
        sfm_th = self.default_parms['SF_PrimThresh']
        freq_th = self.default_parms['F_PrimThresh']
        spoken_frames = []
        number_of_silence_frames = 0
        for ind in range(features.shape[0]):
            debug_log = ""
            counter = 0
            if (features[ind][0] - self.min_energy) >= energy_th:
                debug_log += "energy "
                counter += 1
            if (features[ind][1] - self.min_sfm) >= sfm_th:
                debug_log += "sfm "
                counter += 1
            if (features[ind][2] - self.min_freq) >= freq_th:
                counter += 1
                debug_log += "Freq "
            if counter > 1:
                spoken_frames.append(True)
            else:
                spoken_frames.append(False)
                self.min_energy = (features[ind][0] + number_of_silence_frames *
                              self.min_energy) / (number_of_silence_frames + 1)
                energy_th = self.default_parms['Energy_PrimThresh'] * math.log(self.min_energy)
                number_of_silence_frames += 1
            #print (debug_log)
        del features
        min_frames_in_silence = int(round(self.default_parms['Min_Silence'] *
                                          float(sampling_frequency) / frame_size))
        if min_frames_in_silence < 0:
            min_frames_in_silence = 0
        min_frames_in_speech = int(round(self.default_parms['Min_Speech'] *
                                         float(sampling_frequency) / frame_size))
        if min_frames_in_speech < 0:
            min_frames_in_speech = 0
        sound_duration = (n_data - 2.0) / (2.0 * float(sampling_frequency))
        bounds_of_speech = []
        for cur_speech_frame in smooth_spoken_frames(spoken_frames,
                                                     min_frames_in_silence,
                                                     min_frames_in_speech):
            init_time = cur_speech_frame[0] * FRAME_DURATION
            fin_time = cur_speech_frame[1] * FRAME_DURATION
            if fin_time > sound_duration:
                fin_time = sound_duration
            bounds_of_speech.append((init_time, fin_time))
        del spoken_frames
        return bounds_of_speech 
        
    


