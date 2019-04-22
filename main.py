import pyaudio, wave
import numpy as np
import struct
import subprocess
import json
from VoiceActivityDetection import VoiceActivityDetection as VAD
from SpeakerRecognition import SpeakerPredictor
from SpeechRecognition import SpeechRecognizer

FRAME_DURATION = 0.01
INIT_SILENCE_FRAMES = 30
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 1
WAVE_OUTPUT_FILENAME = "file.wav"
SAVE_FILES = True

COMMAND_MAP = json.load( open( "/home/libin/project/Config/Commands.json" ) )

def RunCommand(prediction):
    subprocess.Popen(COMMAND_MAP[prediction]["Command to run"])
    
def run(vad):
    audio = pyaudio.PyAudio()
    predict_spk = SpeakerPredictor()
    predict_spk.load_models("SpeakerRecognition/Speakers_models/")
    speech_predict = SpeechRecognizer()
    speech_predict.load_models("SpeechRecognition/Speech_Models/")
    status_file = "/home/libin/project/temp/status"
    vad_status_file = "/home/libin/project/temp/vad_out"
    with open("RegisteredSpeaker.txt", 'r') as fp:
        registered_speakers = [spk.strip() for spk in fp]
    # start Recording
    print ("recording...")
    frames = []
    human_speech = [b'', b'', b'']
    count = 0
    sound_whole = []
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    SECONDS_PRED = 2
    index = 0
    while True:
        # file used for stoping Application in case of config change
        with open(status_file, 'r') as fp:
            if fp.read().strip() == '0':
                with open(status_file, 'w') as f:
                    f.write("1")
                vad.read_config("Config/vad.cfg")
                vad.initalize_VAD_min()
        try:
            # sampling audio for RECORD_SECONDS
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)
                
            # joining frames for RECORD_SECONDS
            sound_data_joined = b''.join(frames)
            
            #detcting spoken regions
            bounds_of_speech = list(vad.detect_spoken_frames(sound_data_joined, RATE))
            #concatinating spoken regions
            for (b, e) in bounds_of_speech:
                if e-b > 0.2:
                    human_speech[count] += (sound_data_joined[2 * int(len(sound_data_joined) * (b/RECORD_SECONDS) * 0.5):
                                                          2 * int(min(len(sound_data_joined) * (e/RECORD_SECONDS) * 0.5 + 1,
                                                                      len(sound_data_joined)*0.5))])
                    if SAVE_FILES:
                        waveFile = wave.open(str(index) + "speech" + WAVE_OUTPUT_FILENAME, 'wb')
                        waveFile.setnchannels(CHANNELS)
                        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
                        waveFile.setframerate(RATE)
                        waveFile.writeframes(human_speech[count])
                        waveFile.close()
                        index += 1
            sound_whole += frames
            frames = []
            
            # set vad value (for 1 second) for using in UI
            with open(vad_status_file, "w") as fp:
                if len(human_speech[count]) >= 0.4 * len(sound_data_joined):
                    fp.write("1")
                else:
                    fp.write("0")
            count = (count + 1) % SECONDS_PRED
            
            # concatinate speech for 2 seconds
            speech = human_speech[count] + human_speech[(count + 1) % SECONDS_PRED] #+ human_speech[(count + 2) % SECONDS_PRED]
            human_speech[count] = b''
            
            # decode binary speech signal
            if len(speech) > 0:
                speech_signal = np.empty((int(len(speech) / 2),))
                for ind in range(speech_signal.shape[0]):
                    speech_signal[ind] = float(struct.unpack('<h', speech[(ind * 2):(ind * 2 + 2)])[0])
                success, speaker = predict_spk.predict_speaker(speech_signal, RATE)
                #if speaker in registered_speakers:
                prediction =  speech_predict.predit_speech(speech_signal, RATE)
                print prediction
                if prediction != 'Silence':
                    human_speech = [b'', b'', b'']
                    RunCommand(prediction)
        except KeyboardInterrupt:
            break

    # stop Recording
    stream.stop_stream()
    stream.close()
    audio.terminate()
    if SAVE_FILES:
        waveFile = wave.open("speech" + WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(speech)
        waveFile.close()
        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(sound_whole))
        waveFile.close()


vad = VAD()
run(vad)
