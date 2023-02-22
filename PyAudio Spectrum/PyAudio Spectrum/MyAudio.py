"""
this is a stripped down version of the SWHear class.
It's designed to hold only a single audio sample in memory.
check my githib for a more complete version:
    http://github.com/swharden
"""

import pyaudio
import time
import numpy as np
import threading


def getFFT(data, rate):
    """Given some data and rate, returns FFTfreq and FFT (half)."""
    data = data*np.hamming(len(data))
    fft = np.fft.fft(data)
    fft = np.abs(fft)
    #fft = 10*np.log10(fft)
    freq = np.fft.fftfreq(len(fft), 1./rate)
    return freq[:int(len(freq)/2)], fft[:int(len(fft)/2)]


class MyAudio():
    """
    The MyAudio class is provides access to recorded and play 
    audio data.
    
    Arguments:
        
        device - the number of the sound card input to use. Leave blank
        to automatically detect one.
        
        rate - sample rate to use. Defaults to something supported.
        
        updatesPerSecond - how fast to record new data. Note that smaller
        numbers allow more data to be accessed and therefore high
        frequencies to be analyzed if using a FFT later
    """

    def __init__(self, inputDevice=None, outputDevice=None, sampleRate=None, updatesPerSecond=10):
        
        self.pa = pyaudio.PyAudio()
        
        self.input_device = inputDevice
        self.output_device = outputDevice
        self.rate = sampleRate        
        self.updatesPerSecond = updatesPerSecond
        self.chunk = 0 
        self.chunksRead = 0
        self.played_frames = 0
        
        self.valid_input_devices()
        self.valid_output_devices()
        
        
    def close(self):
        """Gently detach from things."""
        print("Sending Stream Termination Command...")
        self.keepRecording = False # the threads should self-close
        self.keepPlaying = False # the threads should self-close
        while(self.t.isAlive()): # wait for all threads to close
            time.sleep(0.1)
        self.in_stream.stop_stream()
        self.pa.terminate()
        print("Stream Terminated.")

        
    ###########################################################################    
    ### RECORDING
    ########################################################################### 
    
    def in_stream_start(self):
        self.in_stream_init()
        print("Starting Input Stream")
        self.keepRecording=True
        self.in_data = None
        self.fft = None
        #self.fft_filtered = None
        self.in_stream = self.pa.open(format=pyaudio.paInt16,
                                      channels=1,
                                      input=True,
                                      input_device_index=self.input_device,
                                      rate=self.rate,
                                      frames_per_buffer=self.chunk)
        self.in_stream_thread_new()     
        
        
    def in_stream_init(self):
        if self.input_device is None: # if no input device is selected use the first one
            self.input_device = self.input_devices[0]        
        if self.rate is None:
            self.rate = int(self.pa.get_device_info_by_index(self.input_device)['defaultSampleRate'])
        self.chunk = int(self.rate/self.updatesPerSecond) # hold ... of a seconds in memory
        if not self.test_input_device(self.input_device, self.rate):
            print('The input device or sample rate is not valid.')
            
        self.datax = np.arange(self.chunk)/float(self.rate)

        print('Recording from "%s" (Device %d) at %d Hz' % (self.pa.get_device_info_by_index(self.input_device)['name'], self.input_device, self.rate))
         
        
        ### SYSTEM TESTS
    
    def valid_input_devices(self):
        self.input_devices = []
        self.input_device_names = []
        for device_index in range(self.pa.get_device_count()):
            if self.test_input_device(device_index):
                self.input_devices.append(device_index)
                self.input_device_names.append(self.pa.get_device_info_by_index(device_index)['name'])
    
        
    def test_input_device(self, device_index, rate=None):
        try:
            info = self.pa.get_device_info_by_index(device_index)
            if rate is None:
                rate = int(info["defaultSampleRate"])
            stream = self.pa.open(format=pyaudio.paInt16,
                                  channels=1,
                                  input=True,
                                  input_device_index=device_index,
                                  rate=rate,
                                  frames_per_buffer=self.chunk)
            stream.close()
            return True
        except:
            return False
        
            
    ### STREAM HANDLING

    def in_stream_thread_new(self):
        self.t = threading.Thread(target=self.in_stream_readchunk)
        self.t.start()
      
        
    def in_stream_readchunk(self):
        '''reads input data and relaunches itself'''
        try:
            self.in_data = np.fromstring(self.in_stream.read(self.chunk), dtype=np.int16)
            self.f, self.fft = getFFT(self.in_data, self.rate)

        except Exception as e:
            print("Exception! Terminating...")
            print(e, 5*'\n')
            self.keepRecording = False
            
        if self.keepRecording:
            self.in_stream_thread_new()
        else:
            self.in_stream.close()
            #self.pa.terminate()
            print("Stream Stopped.")
            
        self.chunksRead += 1
        
    def set_input_device(self, device_index): 
        if self.test_input_device(device_index, self.rate):
            self.input_device = device_index
            self.keepRecording = False
            while(self.t.isAlive()): # Wait for the recording thread to close
                time.sleep(0.1)
            self.in_stream_start()   
            return True
        else:
            return False
              
        
    ###########################################################################    
    ### PLAYING
    ########################################################################### 
       
    def out_stream_start(self, out_data):
        self.out_stream_init()
        print('Starting Output Stream')
        self.keepPlaying = True
        self.out_data = out_data
        self.played_frames = 0
        self.out_stream = self.pa.open(format=pyaudio.paFloat32,
                                       channels=1, 
                                       output=True, 
                                       output_device_index=self.output_device,
                                       rate=self.rate,
                                       stream_callback=self.out_stream_callback)
        
    def out_stream_init(self):      
        if not self.test_output_device(self.output_device, self.rate):
            print("No valid ouput device...")
        print('Playing from "%s" (Device %d) at %d Hz' % (self.pa.get_device_info_by_index(self.output_device)["name"], self.output_device, self.rate))
        
            
    def valid_output_devices(self):
        self.output_devices = []
        self.output_device_names = []
        for device_index in range(self.pa.get_device_count()):
            if self.test_output_device(device_index):
                self.output_devices.append(device_index)
                self.output_device_names.append(self.pa.get_device_info_by_index(device_index)['name'])
                
        if self.output_device is None:  # if no output device is selected use the first one
            self.output_device = self.output_devices[0]
           

    def test_output_device(self, device_index, rate=None):
        try:
            self.info = self.pa.get_device_info_by_index(device_index)
            if not self.info["maxInputChannels"] == 0:
                return False
            stream = self.pa.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=44100,
                                  output=True,
                                  output_device_index=device_index)
            stream.close()
            return True
        except:
            return False
         
            
    def out_stream_callback(self, in_data, frame_count, time_info, status):
        data = self.out_data[self.played_frames:self.played_frames+frame_count].astype(np.float32).tostring()
        self.played_frames += frame_count
        if self.keepPlaying:
            flag = pyaudio.paContinue
        else:
            flag = pyaudio.paComplete            
        return data, flag
                

    def set_output_device(self, device_index):
        if self.test_output_device(device_index):
            self.output_device = device_index
            return True
        else:
            return False
            
        
'''
if __name__=="__main__":
    ear=MyAudio(updatesPerSecond=10) # optinoally set sample rate here
    ear.stream_start() #goes forever
    lastRead=ear.chunksRead
    while True:
        while lastRead==ear.chunksRead:
            time.sleep(.01)
        print(ear.chunksRead,len(ear.data))
        lastRead=ear.chunksRead
    print("DONE")
'''
