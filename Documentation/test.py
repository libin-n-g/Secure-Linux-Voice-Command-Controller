# import numpy as np              
 
# import wave
 
# import struct
 
# import matplotlib.pyplot as plt
 
# # frequency is the number of times a wave repeats a second
 
# frequency = 1000
 
# num_samples = 48000
 
# # The sampling rate of the analog to digital convert
 
# sampling_rate = 48000.0
 
# amplitude = 16000
 
# file = "test.wav"

# sine_wave = [np.sin(2 * np.pi * frequency * x/sampling_rate) for x in range(num_samples)]

# nframes=num_samples
 
# comptype="NONE"
 
# compname="not compressed"
 
# nchannels=1
 
# sampwidth=2

# wav_file=wave.open(file, 'w')
 
# wav_file.setparams((nchannels, sampwidth, int(sampling_rate), nframes, comptype, compname))

# for s in sine_wave:
#     wav_file.writeframes(struct.pack('h', int(s*amplitude)))

#!/usr/bin/env python3
#
# Released under the HOT-BEVERAGE-OF-MY-CHOICE LICENSE: Bastian Rieck wrote
# this script. As long you retain this notice, you can do whatever you want
# with it. If we meet some day, and you feel like it, you can buy me a hot
# beverage of my choice in return.

import numpy
import scipy.io.wavfile
import scipy.stats
import sys

def chunks(l, k):
  """
  Yields chunks of size k from a given list.
  """
  for i in range(0, len(l), k):
    yield l[i:i+k]

def shortTermEnergy(frame):
  """
  Calculates the short-term energy of an audio frame. The energy value is
  normalized using the length of the frame to make it independent of said
  quantity.
  """
  return sum( [ abs(x)**2 for x in frame ] ) / len(frame)

def rateSampleByVariation(chunks):
  """
  Rates an audio sample using the coefficient of variation of its short-term
  energy.
  """
  energy = [ shortTermEnergy(chunk) for chunk in chunks ]
  return scipy.stats.variation(energy)

def zeroCrossingRate(frame):
  """
  Calculates the zero-crossing rate of an audio frame.
  """
  signs             = numpy.sign(frame)
  signs[signs == 0] = -1

  return len(numpy.where(numpy.diff(signs))[0])/len(frame)

def rateSampleByCrossingRate(chunks):
  """
  Rates an audio sample using the standard deviation of its zero-crossing rate.
  """
  zcr = [ zeroCrossingRate(chunk) for chunk in chunks ]
  return numpy.std(zcr)

def entropyOfEnergy(frame, numSubFrames):
  """
  Calculates the entropy of energy of an audio frame. For this, the frame is
  partitioned into a number of sub-frames.
  """
  lenSubFrame = int(numpy.floor(len(frame) / numSubFrames))
  shortFrames = list(chunks(frame, lenSubFrame))
  energy      = [ shortTermEnergy(s) for s in shortFrames ]
  totalEnergy = sum(energy)
  energy      = [ e / totalEnergy for e in energy ]

  entropy = 0.0
  for e in energy:
    if e != 0:
      entropy = entropy - e * numpy.log2(e)

  return entropy

def rateSampleByEntropy(chunks):
  """
  Rates an audio sample using its minimum entropy.
  """
  entropy = [ entropyOfEnergy(chunk, 20) for chunk in chunks ]
  return numpy.min(entropy)

#
# main
#

# Frame size in ms. Will use this quantity to collate the raw samples
# accordingly.
frameSizeInMs = 0.01

frequency          = 44100 # Frequency of the input data
numSamplesPerFrame = int(frequency * frameSizeInMs)

data        = scipy.io.wavfile.read( sys.argv[1] )
chunkedData = list(chunks(list(data[1]), numSamplesPerFrame))

variation = rateSampleByVariation(chunkedData)
zcr       = rateSampleByCrossingRate(chunkedData)
entropy   = rateSampleByEntropy(chunkedData)

print("Coefficient of variation  = %f\n"
      "Standard deviation of ZCR = %f\n"
      "Minimum entropy           = %f" % (variation, zcr, entropy) )

if variation >= 1.0:
  print("Coefficient of variation suggests that the sample contains speech")

if zcr >= 0.05:
  print("Standard deviation of ZCR suggests that the sample contains speech")

if entropy < 2.5:
  print("Minimum entropy suggests that the sample contains speech")
