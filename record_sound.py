import pyaudio
import wave
import threading

class RecordAudio(threading.Thread):
    def __init__(self, output_file):
        threading.Thread.__init__(self)
        self.recording = False
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024
        self.wave_output_filename = output_file 
        self.terminate_thread = False

    def run(self):
        audio = pyaudio.PyAudio()
        self.recording = True
        # start Recording
        stream = audio.open(format=self.format, channels=self.channels,
                rate=self.rate, input=True,
                frames_per_buffer=self.chunk)
        frames = []
        while self.recording:
            for i in range(0, int(self.rate / self.chunk * 1)):
                data = stream.read(self.chunk)
                frames.append(data)
            if self.terminate_thread:
                return
        
        # stop Recording
        stream.stop_stream()
        stream.close()
        audio.terminate()

        waveFile = wave.open(self.wave_output_filename, 'wb')
        waveFile.setnchannels(self.channels)
        waveFile.setsampwidth(audio.get_sample_size(self.format))
        waveFile.setframerate(self.rate)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()
    
    def change_output_file(self, new_file):
        self.wave_output_filename = new_file
