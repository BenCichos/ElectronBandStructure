import sys
from PyQt5.QtWidgets import QMainWindow, QDialog, QFileDialog, QWidget, QApplication, QMessageBox
from PyQt5.uic import loadUi

from PyQt5.QtCore import QSettings

import pyqtgraph as pg
#import time

import numpy as np
from pyqtgraph import QtGui, QtCore

import MyAudio

class FFTWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        loadUi('FFTWindow.ui', self)
        
        gLayout = pg.GraphicsLayoutWidget()  
        self.layout.addWidget(gLayout)
        self.p = gLayout.addPlot()
        self.p.showAxis('top')
        self.p.showAxis('right')
        self.p.setLabels(left='Amplitude [arb. unit.]', bottom='Frequency [Hz]')
        self.p.getAxis('top').setStyle(showValues=False)
        self.p.getAxis('right').setStyle(showValues=False)
        self.p.getAxis('top').setHeight(10)
        self.p.getAxis('right').setWidth(15)

        
class SignalWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        loadUi('SignalWindow.ui', self)
        
        gLayout = pg.GraphicsLayoutWidget()  
        self.layout.addWidget(gLayout)   
        self.p = gLayout.addPlot()
        self.p.showAxis('top')
        self.p.showAxis('right')
        self.p.setLabels(left='Amplitude [arb. unit.]', bottom='Time [s]')
        self.p.getAxis('top').setStyle(showValues=False)
        self.p.getAxis('right').setStyle(showValues=False)
        self.p.getAxis('top').setHeight(10)
        self.p.getAxis('right').setWidth(15)

        
        
class DevicesWindow(QDialog):
    def __init__(self):
        super().__init__(None,  QtCore.Qt.WindowCloseButtonHint)
        
        loadUi('DevicesWindow.ui', self)
        
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        
        self.outputDevicesComboBox.currentIndexChanged.connect(self.outputDeviceChanged) 
        self.inputDevicesComboBox.currentIndexChanged.connect(self.inputDeviceChanged)
        self.inputDevice = 0
        self.inputDevices = []
        self.outputDevice = 0
        self.outputDevices = []

    def okClicked(self):
        self.close()
        
    def inputDeviceChanged(self, index):
        self.inputDevice = self.inputDevices[index]
        print(self.inputDevice) 
        
    def outputDeviceChanged(self, index):
        self.outputDevice = self.outputDevices[index]
        print(self.outputDevice)
    

        
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        #pg.setConfigOptions(antialias=True)
        
        loadUi('MainWindow.ui', self)
           
        gLayout = pg.GraphicsLayoutWidget() 
        self.layout.addWidget(gLayout)
        self.p = gLayout.addPlot()
         
        self.p.showAxis('top')
        self.p.showAxis('right')
        self.p.setLabels(left='Amplitude [arb. unit.]', bottom='Frequency [Hz]')
        self.p.getAxis('top').setStyle(showValues=False)
        self.p.getAxis('right').setStyle(showValues=False)
        self.p.getAxis('top').setHeight(10)
        self.p.getAxis('right').setWidth(15)
        self.p.setRange(xRange=[100, 10000], padding=0)

        #lr = pg.LinearRegionItem(values=[1000, 2500], movable=False) 
        #self.p.addItem(lr)

                # Restore settings of the previous session from the Settings.ini file
        self.settings = QSettings('Settings.ini', QSettings.IniFormat)
        self.startFrequency = int(self.settings.value('StartFrequency', 100))
        self.startFrequencySpinBox.setValue(self.startFrequency)
        self.stopFrequency = int(self.settings.value('StopFrequency', 10000))
        self.stopFrequencySpinBox.setValue(self.stopFrequency) 
        self.stepSize = int(self.settings.value('StepSize', 10))
        self.stepSizeSpinBox.setValue(self.stepSize) 
        self.timePerStep = int(self.settings.value('TimePerStep', 50))
        self.timePerStepSpinBox.setValue(self.timePerStep) 
        

        
        self.pList = [self.p.plot([], [], pen=pg.mkPen(color='b'), antialias=True), 
                      self.p.plot([], [], pen=pg.mkPen(color='r'), antialias=True),
                      self.p.plot([], [], pen=pg.mkPen(color='k'), antialias=True),
                      self.p.plot([], [], pen=pg.mkPen(color='m'), antialias=True),
                      self.p.plot([], [], pen=pg.mkPen(color='c'), antialias=True)]

        self.p.setLimits(xMin=self.startFrequency, xMax=self.stopFrequency, yMin=0)
        
        self.startFrequencySpinBox.valueChanged.connect(self.startFrequencyChanged)  
        self.stopFrequencySpinBox.valueChanged.connect(self.stopFrequencyChanged)  
        self.stepSizeSpinBox.valueChanged.connect(self.stepSizeChanged) 
        self.timePerStepSpinBox.valueChanged.connect(self.timePerStepChanged) 
        
        self.startButton.clicked.connect(self.startStopClicked) 
        self.clearButton.clicked.connect(self.clearSpectrumClicked) 
        self.start = False
        
        # File
        self.actionSaveSpectrumAs.triggered.connect(self.saveSpectrumAs)
        self.actionOpenSpectrum.triggered.connect(self.openSpectrum)
        self.actionExit.triggered.connect(self.close)
                
        # Windows
        self.actionFFTWindow.triggered.connect(self.showFFTWindow)
        self.actionSignalWindow.triggered.connect(self.showSignalWindow)
        # Settings
        self.actionDevices.triggered.connect(self.showDevicesWindow)
        # Help
        self.actionAbout.triggered.connect(self.aboutClicked)

        self.spectrum1RadioButton.toggled.connect(lambda:self.spectrumRadioButtonChanged(self.spectrum1RadioButton))
        self.spectrum2RadioButton.toggled.connect(lambda:self.spectrumRadioButtonChanged(self.spectrum2RadioButton))
        self.spectrum3RadioButton.toggled.connect(lambda:self.spectrumRadioButtonChanged(self.spectrum3RadioButton))
        self.spectrum4RadioButton.toggled.connect(lambda:self.spectrumRadioButtonChanged(self.spectrum4RadioButton))
        self.spectrum5RadioButton.toggled.connect(lambda:self.spectrumRadioButtonChanged(self.spectrum5RadioButton))
        self.selectedSpectrum = 0
        
        
        self.fftWindow = FFTWindow()
        self.fftWindow.p.setRange(xRange=[100, 20000], padding=0)
        self.fftWindow.p.setRange(yRange=[0, 1], padding=0)
        self.maxFFT = 0
        
        self.c1 = self.fftWindow.p.plot([100, 100],[0, 1])
        self.c2 = self.fftWindow.p.plot([20000, 20000],[0, 1])
        
        item = pg.FillBetweenItem(curve1=None, curve2=None, brush=0.8)
        self.box = self.fftWindow.p.addItem(item)

        
        self.signalWindow = SignalWindow()
        #self.signalWindow.p.setRange(xRange=[0, 0.01], padding=0)
            
        self.audio = MyAudio.MyAudio(updatesPerSecond=20)
        self.audio.in_stream_start()
                
        self.devicesWindow = DevicesWindow()
        
        self.inputDevice = self.audio.input_device
        self.devicesWindow.inputDevice = self.inputDevice
        self.devicesWindow.inputDevices = self.audio.input_devices
        self.devicesWindow.inputDevicesComboBox.addItems(self.audio.input_device_names)
        
        self.outputDevice = self.audio.output_device
        self.devicesWindow.outputDevice = self.outputDevice
        self.devicesWindow.outputDevices = self.audio.output_devices
        self.devicesWindow.outputDevicesComboBox.addItems(self.audio.output_device_names)
            
        
        self.xDataList = []
        self.yDataList = [] 
        for i in range(5):
            self.xDataList.append([])
            self.yDataList.append([])
         
        self.pen = pg.mkPen(color='b') 
        

        
         
    def spectrumRadioButtonChanged(self, radioButton):
        if radioButton.text() == 'Spectrum 1' and radioButton.isChecked():
            self.selectedSpectrum = 0 
        if radioButton.text() == 'Spectrum 2' and radioButton.isChecked():
            self.selectedSpectrum = 1             
        if radioButton.text() == 'Spectrum 3' and radioButton.isChecked():
            self.selectedSpectrum = 2         
        if radioButton.text() == 'Spectrum 4' and radioButton.isChecked():
            self.selectedSpectrum = 3           
        if radioButton.text() == 'Spectrum 5' and radioButton.isChecked():
            self.selectedSpectrum = 4
        
        
    def aboutClicked(self):
        QMessageBox.about(self, 'About', 'This program has been developed to measure sound spectra. '
                          + 'It is based on PyAudio and the PyQt and PyQtGraph libary.' + 2*'\n'
                          + 'Martin Fränzl')    
            
        
    def saveSpectrumAs(self):
        options = QFileDialog.Options()
        #options |= QFileDialog.DontUseNativeDialog
        file,_ = QFileDialog.getSaveFileName(self, 'Save Spectrum As...', '', 'All Files (*);;Text Files (*.txt)', options=options)
        if file:
            np.savetxt(file, np.transpose([self.xDataList[self.selectedSpectrum], self.yDataList[self.selectedSpectrum]]), fmt='%.0f')    
    
    
    def openSpectrum(self):
        options = QFileDialog.Options()
        #options |= QFileDialog.DontUseNativeDialog
        file, _ = QFileDialog.getOpenFileName(self,'Open Spectrum...', '', 'Text Files (*.txt);;All Files (*)', options=options)
        if file:
            data = np.transpose(np.loadtxt(file))
            self.xDataList[self.selectedSpectrum] = data[0]
            self.yDataList[self.selectedSpectrum] = data[1]
            self.pList[self.selectedSpectrum].setData(self.xDataList[self.selectedSpectrum], self.yDataList[self.selectedSpectrum])
            #self.p.setRange(yRange=[0, np.max(self.ydata)], padding=0)
                    
    def showFFTWindow(self):
        self.fftWindow.show()


    def showSignalWindow(self):
        self.signalWindow.show()
    
    
    def showDevicesWindow(self):
        
        if self.devicesWindow.exec_() == QtGui.QDialog.Accepted:
            if self.devicesWindow.inputDevice != self.inputDevice:
                if self.audio.set_input_device(self.devicesWindow.inputDevice):
                    self.inputDevice = self.devicesWindow.inputDevice
            if self.devicesWindow.outputDevice != self.outputDevice:
                if self.audio.set_output_device(self.devicesWindow.outputDevice):
                    self.outputDevice = self.devicesWindow.outputDevice
        else: # QtGui.QDialog.Rejected 
            self.devicesWindow.inputDevice = self.inputDevice
            self.devicesWindow.inputDevicesComboBox.setCurrentIndex(self.devicesWindow.inputDevices.index(self.inputDevice))
            self.devicesWindow.outputDevice = self.outputDevice
            self.devicesWindow.outputDevicesComboBox.setCurrentIndex(self.devicesWindow.outputDevices.index(self.outputDevice))
  

            
    def startStopClicked(self):
        if self.start:
            self.start = False
            self.startButton.setText('Start')
            self.audio.keepPlaying = False
            self.clearButton.setEnabled(True)
            self.startFrequencySpinBox.setEnabled(True)
            self.stopFrequencySpinBox.setEnabled(True)
            self.stepSizeSpinBox.setEnabled(True)
            self.timePerStepSpinBox.setEnabled(True)       
            self.spectrumGroupBox.setEnabled(True)
            self.actionDevices.setEnabled(True) 
        else:
            self.start = True
            self.startButton.setText('Stop')
            self.clearButton.setEnabled(False)
            self.startFrequencySpinBox.setEnabled(False)
            self.stopFrequencySpinBox.setEnabled(False)
            self.stepSizeSpinBox.setEnabled(False)
            self.timePerStepSpinBox.setEnabled(False)
            self.timePerStepSpinBox.setEnabled(False)
            self.spectrumGroupBox.setEnabled(False)
            self.actionDevices.setEnabled(False)   
            
            self.xDataList[self.selectedSpectrum] = []
            self.yDataList[self.selectedSpectrum] = []
    
            self.f_index = 0
            self.tmp = 0
            self.freq = np.arange(self.startFrequency, self.stopFrequency + self.stepSize, self.stepSize)
            self.fsteps = self.freq.size
            self.fft_max_list = np.array([])
            #self.fft_max_count = 0
            
            self.f1 = self.startFrequency
            self.f2 = self.stopFrequency
            
            self.dt = 0.001*self.timePerStep*(self.f2 - self.f1)/self.stepSize
            self.t = np.arange(0., self.dt, 1./44100)         
            out_data = np.sin(2*np.pi*((self.f2 - self.f1)*self.t/self.dt/2 + self.f1)*self.t) # chirp
            #out_data = chirp(t, f0=f1, f1=f2, t1=dt, method='linear')

            self.audio.out_stream_start(out_data)
            
            if self.fftWindow.isVisible():
                self.fftWindow.activateWindow()
            
            
    def clearSpectrumClicked(self):  
        self.pList[self.selectedSpectrum].clear()
        self.xDataList[self.selectedSpectrum] = []
        self.yDataList[self.selectedSpectrum] = []
        
        

    def update(self):
        
        if not self.audio.in_data is None and not self.audio.fft is None:

            fft = self.audio.fft 
            self.maxFFT = np.max(np.abs(self.audio.fft))
            
            if self.fftWindow.isVisible():
                self.fftWindow.p.plot(self.audio.f, self.audio.fft/self.maxFFT, pen=pg.mkPen(color='b'), clear=True, antialias=True)       
                #item = pg.FillBetweenItem(curve1=pg.PlotCurveItem(x=[1000,1000], y=[0, 1]), curve2=pg.PlotCurveItem(x=[1500,1500], y=[0, 1]), brush=0.8)
                #self.fftWindow.p.addItem(item)
                if self.start and self.f_index < self.fsteps:
                    fmin = self.freq[self.f_index] - 125
                    fmax = self.freq[self.f_index] + 125
                    #item = pg.FillBetweenItem(curve1=pg.PlotCurveItem(x=[fmin,fmin], y=[0, 1]), curve2=pg.PlotCurveItem(x=[fmax,fmax], y=[0, 1]), brush=0.8)
                    #self.fftWindow.p.addItem(item)
                    self.fftWindow.p.addLine(x=fmin, pen=pg.mkPen(color='k'))
                    self.fftWindow.p.addLine(x=fmax, pen=pg.mkPen(color='k'))
                
            if self.signalWindow.isVisible():
                self.signalWindow.p.plot(self.audio.datax, self.audio.in_data, pen=pg.mkPen(color='b'), clear=True, antialias=True)
                
            if self.start:
                self.f_index = int(self.fsteps*self.audio.played_frames/self.t.size)
                if self.f_index < self.fsteps:
                    fft_max = np.max(fft[np.where(np.logical_and(self.audio.f > self.freq[self.f_index]-125, self.audio.f < self.freq[self.f_index]+125))])
                    self.fft_max_list = np.append(self.fft_max_list, fft_max)
                    if not self.f_index == self.tmp:
                        self.tmp = self.f_index
                        self.xDataList[self.selectedSpectrum] = np.append(self.xDataList[self.selectedSpectrum], self.freq[self.f_index])
                        self.yDataList[self.selectedSpectrum] = np.append(self.yDataList[self.selectedSpectrum], sum(self.fft_max_list)/len(self.fft_max_list))
                        self.pList[self.selectedSpectrum].setData(self.xDataList[self.selectedSpectrum], self.yDataList[self.selectedSpectrum], clear=True)
                        self.fft_max_list = np.array([])

                else:
                    self.start = False
                    self.startButton.setText('Start')
                    self.clearButton.setEnabled(True)
                    self.startFrequencySpinBox.setEnabled(True)
                    self.stopFrequencySpinBox.setEnabled(True)
                    self.stepSizeSpinBox.setEnabled(True)
                    self.timePerStepSpinBox.setEnabled(True)
                    self.spectrumGroupBox.setEnabled(True)
        
        QtCore.QTimer.singleShot(1, self.update) # quickly repeat

    def startFrequencyChanged(self, value):
        self.startFrequency = value
        self.p.setRange(xRange=[self.startFrequency, self.stopFrequency], padding=0)
        self.p.setLimits(xMin=self.startFrequency)
        
    def stopFrequencyChanged(self, value):
        self.stopFrequency = value 
        self.p.setRange(xRange=[self.startFrequency, self.stopFrequency], padding=0)
        self.p.setLimits(xMax=self.stopFrequency)
    
    def stepSizeChanged(self, value):
        self.stepSize = value
        
    def timePerStepChanged(self, value):
        self.timePerStep = value
        
    def closeEvent(self, e):
        self.settings.setValue('StartFrequency', self.startFrequency)
        self.settings.setValue('StopFrequency', self.stopFrequency)
        self.settings.setValue('StepSize', self.stepSize)
        self.settings.setValue('TimePerStep', self.timePerStep)
        self.fftWindow.close()
        self.signalWindow.close()
        self.audio.close()
        e.accept()    
           



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.update() # start with something
    sys.exit(app.exec_())