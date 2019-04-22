import numpy as np
import struct
import pyaudio
import matplotlib.pyplot as plt
from scipy import signal, stats
import math
FRAME_DURATION = 0.01
EPS = 1e-6
INIT_SILENCE_FRAMES = 30
DEFAULT_PARAMS_OF_WEBRTC_ALG = {'Min_Silence': 0.2, 'Min_Speech': 0.1}

class Audio(pyaudio.PyAudio, object):
    """Class which start audio listener"""
    def __init__(self):
        """Constructor"""
        super(Audio, self).__init__()
        self.FORMAT = pyaudio.paInt16 # We use 16bit format p11er sample
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024 # 1024bytes of data red from a buffer
        self.stream = self.open(format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RATE,
                    input=True,
                    frames_per_buffer=self.CHUNK)
        self.stream_opened = True
        self.graph = False
        self.stream_started = False
    def start_graph(self, length=10000):
        """Creates Graph of given length"""
        self.graph = True
        plt.ion()
        fig = plt.figure()
        self.ax = fig.add_subplot(111)
        x = np.arange(length)
        y = np.random.randn(length)
        self.li, = self.ax.plot(x, y)
        self.ax.set_xlim(0,1000)
        self.ax.set_ylim(-0.5,0.5)
        self.ax.set_title("Raw Audio Signal")
        plt.pause(0.1)
        plt.tight_layout()
    def start_stream(self):
        self.stream.start_stream()
        self.stream_started = True
    def get_audio_chunk(self):
        in_data = self.stream.read(self.CHUNK*5, True)
        self.sound = in_data
        self.audio_data = np.fromstring(in_data, np.int16)
        self.dfft = 10.*np.log10(abs(np.fft.rfft(self.audio_data)))
        if self.graph:
            self.li.set_xdata(np.arange(len(self.audio_data)))
            self.li.set_ydata(self.audio_data)
            plt.pause(0.01)
        return self.audio_data
    def stop_stream(self):
        self.stream.stop_stream()
        self.stream_started = False
    def close_stream(self):
        self.stream.close()
        self.stream_opened = False
    def __del__(self):
        if self.stream_started:
            self.stop_stream()
        if self.stream_opened:
            self.close_stream()
        self.terminate()
    def shortTermEnergy(self):
        def chunks(l, k):
            """
            Yields chunks of size k from a given list.
            """
            for i in range(0, len(l), k):
                yield l[i:i+k]
        STE = []
        for f in chunks(self.audio_data,256):
            STE.append( sum( [ abs(x)**2 for x in f ] ) / float(len(f)))
        return STE

global ax
global li, li1, li2, li3
f,ax = plt.subplots(4)

max_f = 0.0
min_f = 0.0 
# Prepare the Plotting Environment with random starting values
x = np.arange(128)
y = np.random.randn(128)

# Plot 0 is for raw audio data
li, = ax[0].plot(x, y)
ax[0].set_xlim(0,128)
ax[0].set_ylim(0,400000000)
ax[0].set_title("Short-time Energy")
# Plot 1 is for the FFT of the audio
li2, = ax[1].plot(x, y)
ax[1].set_xlim(0,128)
ax[1].set_ylim(1,10)
ax[1].set_title("Spectral Flatness Measure")
# Plot 0 is for raw audio data
li3, = ax[2].plot(x, y)
ax[2].set_xlim(0,128)
ax[2].set_ylim(0,4500)
ax[2].set_title("Most Dominant Frequency Component")
# Plot 1 is for the FFT of the audio
li4, = ax[3].plot(x, y)
ax[3].set_xlim(0,512)
ax[3].set_ylim(-1,1)
ax[3].set_title("Wave File")

# Show the plot, but without blocking updates
plt.pause(0.01)
plt.tight_layout()

def calculate_features_for_VAD(sound_frames, frequencies_axis, spectrogram):
    features = np.empty((spectrogram.shape[0], 3))
    # smooted_spectrogram, smoothed_frequencies_axis = smooth_spectrogram(spectrogram, frequencies_axis, 24)
    for time_ind in range(spectrogram.shape[0]):
        mean_spectrum = spectrogram[time_ind].mean()
        if mean_spectrum > 0.0:
            sfm = -10.0 * math.log10(stats.gmean(spectrogram[time_ind]) / mean_spectrum)
        else:
            sfm = 0.0
        # max_freq = smoothed_frequencies_axis[smooted_spectrogram[time_ind].argmax()]
        max_freq = frequencies_axis[spectrogram[time_ind].argmax()]
        features[time_ind][0] = np.square(sound_frames[time_ind]).mean()
        features[time_ind][1] = sfm
        features[time_ind][2] = max_freq
    """medfilt_order = 3
    for feature_ind in range(features.shape[0]):
        features[feature_ind] = signal.medfilt(features[feature_ind], medfilt_order)"""
    return features
sound = []
features = [[],[],[]]
def show_VAD_features(sound_data, sampling_frequency, max_f):
    assert sampling_frequency >= 8000, 'Sampling frequency is inadmissible!'
    n_data = len(sound_data)
    assert (n_data > 0) and ((n_data % 2) == 0), 'Sound data are wrong!'
    frame_size = int(round(FRAME_DURATION * float(sampling_frequency)))
    n_fft_points = 2
    while n_fft_points < frame_size:
        n_fft_points *= 2
    sound_signal = np.array(map( lambda x : float(x), np.fromstring(sound_data, 'Int16')));
    frequencies_axis, time_axis, spectrogram = signal.spectrogram(
        sound_signal, fs=sampling_frequency, window='hamming', nperseg=frame_size, noverlap=0, nfft=n_fft_points,
        scaling='spectrum', mode='psd'
    )
    spectrogram = spectrogram.transpose()
    if spectrogram.shape[0] <= INIT_SILENCE_FRAMES:
        return []
    if (sound_signal.shape[0] % frame_size) == 0:
        sound_frames = np.reshape(sound_signal, (spectrogram.shape[0], frame_size))
    else:
        sound_frames = np.reshape(sound_signal[0:int(sound_signal.shape[0] / frame_size) * frame_size],
                                     (spectrogram.shape[0], frame_size))
    _features = calculate_features_for_VAD(sound_frames, frequencies_axis, spectrogram).transpose()
    time_axis = time_axis.transpose()
    del spectrogram
    del frequencies_axis
    #plt.subplot(411)
    features[0].extend(_features[0])
    features[1].extend(_features[1])
    features[2].extend(_features[2])
    ax[0].set_xlim(0,len(features[0]))
    ax[0].set_ylim(min(features[0]),max(features[0]))
    li.set_xdata(np.arange(len(features[0])))
    li.set_ydata(features[0])
    #plt.title('Short-time Energy')
    #plt.grid(True)
    #plt.subplot(412)
    ax[1].set_xlim(0,len(features[1]))
    ax[1].set_ylim(min(features[1]),max(features[1]))
    li2.set_xdata(np.arange(len(features[1])))
    li2.set_ydata(features[1])
    #plt.title('Spectral Flatness Measure')
    #plt.grid(True)
    #plt.subplot(413)
    ax[2].set_xlim(0,len(features[2]))
    ax[2].set_ylim(min(features[2]),max(features[2]))
    #    print max(features[2]), min(features[2])
    li3.set_xdata(np.arange(len(features[2])))
    li3.set_ydata(features[2])
    #plt.title('Most Dominant Frequency Component')
    #plt.grid(True)
    #plt.subplot(414)
    x = np.repeat(time_axis, 4)
    y = []
    for time_ind in range(time_axis.shape[0]):
        y += [sound_frames[time_ind][0], sound_frames[time_ind].max(), sound_frames[time_ind].min(),
              sound_frames[time_ind][-1]]
    y = np.array(y)
    sound.extend(y)
    ax[3].set_xlim(0,len(sound))
    ax[3].set_ylim(min(sound),max(sound))
    li4.set_xdata(np.arange(len(sound)))
    li4.set_ydata(sound)
    plt.pause(0.01)
    del sound_frames
    del time_axis
    return max_f


import time
time.sleep(2)
s = Audio()
#s.start_graph()
s.start_stream()
keep_going = True
s_old = 100
a = 10
while s.stream.is_active():
    sound_frames = s.get_audio_chunk()
    max_f = show_VAD_features(s.sound, 8000, max_f)
    a-=1
    print a
    if a==0:
        time.sleep(1000)
del s
