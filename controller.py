import sys
from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QTabWidget, QGraphicsScene, QFileDialog, QMessageBox, QGraphicsView

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Slot, Qt, QDir, QObject, QEvent
from PySide6.QtGui import QPixmap, QIcon, QImageReader, QGuiApplication, QPainter, QImage

import imageio
import numpy as np
import matplotlib.pyplot as plt
from PIL import ImageQt, Image

import time
from queue import Queue
from PySide6.QtCore import QRunnable, Slot, QThreadPool, Signal, QObject, QMutex
from threading import Event

import model

class WorkerSignals(QObject):
    processed = Signal(object)
    terminated = Signal()

class Worker(QRunnable):
    def __init__(self):
        super(Worker, self).__init__()
        self.signals = WorkerSignals()
        self.terminate = False
        self.new_data_arrived = Event()
        self.mutex = QMutex()
        self.f = None
        self.params = None
        self.split_dimensions = True
        self.threadpool = QThreadPool()

    @Slot()
    def run(self):
        print("Worker started")
        while not self.terminate:
            try:
                self.new_data_arrived.wait(timeout=1)
            except:
                pass

            if self.new_data_arrived.is_set():
                self.mutex.lock()
                self.new_data_arrived.clear()
                f = self.f
                params = self.params
                self.mutex.unlock()

                if len(params[0].shape)==2 or not self.split_dimensions:
                    output = f(*params)
                elif len(params[0].shape)==3:
                    finished_events = []
                    output = []
                    for i in range(params[0].shape[2]):
                        output.append(None)
                        e = Event()
                        finished_events.append(e)
                        params_ = (params[0][:,:,i], *(params[1:]))
                        temp_worker = TemporaryWorker(f, params_, output, i, e)
                        self.threadpool.start(temp_worker)
                    for e in finished_events:
                        e.wait()
                    output = np.stack(output, axis=2)
                self.signals.processed.emit(np.array(output))
        print("Worker stopped")

    @Slot(object, object)
    def process(self, f, parameters, split_dimensions=True):
        self.mutex.lock()
        self.f = f
        self.params = parameters
        self.split_dimensions = split_dimensions
        self.new_data_arrived.set()
        self.mutex.unlock()

class TemporaryWorker(QRunnable):
    def __init__(self, f, params, output, idx, finished_event):
        super(TemporaryWorker, self).__init__()
        self.f = f
        self.params = params
        self.output = output
        self.idx = idx
        self.finished_event = finished_event

    @Slot()
    def run(self):
        #print("TemporaryWorker started")
        self.output[self.idx] = self.f(*self.params)
        self.finished_event.set()
        #print("TemporaryWorker stopped")


class MouseDetector(QObject):

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if isinstance(obj, QGraphicsView):
                #print('mouse pressed. ObjectName: ', obj.objectName())
                self.getPos(event)
                scene_position = obj.mapToScene(int(event.position().x()), int(event.position().y()))

                if self.app.select_x_spinbox is not None:
                    self.app.select_x_spinbox.setValue(scene_position.x())
                    self.app.select_x_spinbox = None
                if self.app.select_y_spinbox is not None:
                    self.app.select_y_spinbox.setValue(scene_position.y())
                    self.app.select_y_spinbox = None
                #print(scene_position)
        return super(MouseDetector, self).eventFilter(obj, event)

    def getPos(self, event):
        x = event.position().x()
        y = event.position().y()
        #print(x, y)


class MyApplication():
    def __init__(self):
        loader = QUiLoader()
        self.window = loader.load("mainwindow.ui", None)


        #For threading
        QApplication.instance().aboutToQuit.connect(self.exit_handler)
        self.threadpool = QThreadPool()
        self.worker = Worker()
        self.threadpool.start(self.worker)
        self.worker.signals.processed.connect(self.update_image_view, Qt.QueuedConnection)


        self.image = None
        self.preview_image = None
        self.persmap_image = None
        self.images_stack = []

        self.current_tab_idx = 0
        self.current_tab_name = "About"

        self.effects_to_tab_idx = {"Fish Eye Effect":1, "Swirl Effect":2, "Waves Effect":3, 
                                   "Cylinder Anamorphosis":4, "Radial Blur Effect":5,
                                   "Perspective Mapping":6, "Square Eye Effect":7, "Median Blurring":8,
                                   "Gaussian Filtering":9, "Bilateral Filter":10, "Mean Filter":11, "About":0}

        self.parameters = self.get_default_parameters()

        self.fisheye_effect_parameters = [self.window.fisheye_x_slider, self.window.fisheye_y_slider, self.window.fisheye_sigma_slider,
                                          self.window.fisheye_x_spinbox, self.window.fisheye_y_spinbox, self.window.fisheye_sigma_spinbox]

        self.swirl_effect_parameters = [self.window.swirl_x_slider, self.window.swirl_y_slider, self.window.swirl_sigma_slider, self.window.swirl_magnitude_slider,
                                          self.window.swirl_x_spinbox, self.window.swirl_y_spinbox, self.window.swirl_sigma_spinbox, self.window.swirl_magnitude_spinbox]

        self.waves_effect_parameters = [self.window.waves_amplitude_slider, self.window.waves_freq_slider, self.window.waves_phase_slider,
                                          self.window.waves_amplitude_spinbox, self.window.waves_freq_spinbox, self.window.waves_phase_spinbox]

        self.cylinder_effect_parameters = [self.window.cylinder_angle_slider, self.window.cylinder_angle_spinbox]

        self.radial_blur_effect_parameters = [self.window.radial_sigma_slider, self.window.radial_sigma_spinbox]

        self.pers_mapping_parameters = [self.window.persmap_x1_spinbox, self.window.persmap_y1_spinbox, self.window.persmap_x2_spinbox, self.window.persmap_y2_spinbox,
                                        self.window.persmap_x3_spinbox, self.window.persmap_y3_spinbox, self.window.persmap_x4_spinbox, self.window.persmap_y4_spinbox,
                                        self.window.persmap_select1_button, self.window.persmap_select2_button, self.window.persmap_select3_button, self.window.persmap_select4_button]

        self.square_eye_effect_parameters = [self.window.square_eye_x_slider, self.window.square_eye_y_slider, self.window.square_eye_sigma_slider, self.window.square_eye_p_slider,
                                         self.window.square_eye_x_spinbox, self.window.square_eye_y_spinbox, self.window.square_eye_sigma_spinbox, self.window.square_eye_p_spinbox]

        self.median_blur_parameters = [self.window.median_size_slider, self.window.median_size_spinbox]
        
        self.gaussian_blur_parameters = [self.window.gaussian_radius_slider, self.window.gaussian_radius_spinbox]

        self.bilateral_filter_parameters = [self.window.bilateral_sigma_slider, self.window.bilateral_sigma_spinbox,
                                            self.window.bilateral_rho_slider, self.window.bilateral_rho_spinbox]

        self.mean_blur_parameters = [self.window.mean_size_slider, self.window.mean_size_spinbox]

        self.tabs_to_apply_buttons_and_params = {
                                      "Fish Eye Effect": {"button":self.window.fisheye_apply_button, "params":self.fisheye_effect_parameters},
                                      "Swirl Effect": {"button":self.window.swirl_apply_button, "params":self.swirl_effect_parameters},
                                      "Waves Effect": {"button": self.window.waves_apply_button, "params":self.waves_effect_parameters},
                                      "Cylinder Anamorphosis": {"button":self.window.cylinder_apply_button, "params":self.cylinder_effect_parameters},
                                      "Radial Blur Effect": {"button":self.window.radial_apply_button, "params":self.radial_blur_effect_parameters},
                                      "Perspective Mapping": {"button":self.window.persmap_apply_button, "params":self.pers_mapping_parameters},
                                      "Square Eye Effect":{"button":self.window.square_eye_apply_button, "params":self.square_eye_effect_parameters},
                                      "Median Blurring": {"button": self.window.median_apply_button, "params": self.median_blur_parameters},
                                      "Gaussian Filtering": {"button": self.window.gaussian_apply_button, "params": self.gaussian_blur_parameters},
                                      "Bilateral Filter": {"button": self.window.bilateral_apply_button, "params": self.bilateral_filter_parameters},
                                      "Mean Filter": {"button": self.window.mean_apply_button, "params": self.mean_blur_parameters}
                                      }

        self.mainwindow_setup()
        self.window.show()

    # For threading
    def exit_handler(self):
        self.worker.terminate = True

    def mainwindow_setup(self):
        w = self.window
        w.setWindowTitle("Image Processing Tool")
        w.resize(1000,800)

        app_icon = QIcon()
        app_icon.addFile('star_white.png')
        w.setWindowIcon(app_icon)

        w.treeWidget.expandAll()

        self.disable_buttons([w.save_button, w.reset_button, w.undo_button,
                              w.fisheye_apply_button, w.swirl_apply_button,
                              w.waves_apply_button, w.cylinder_apply_button,
                              w.radial_apply_button, w.persmap_apply_button,
                              w.square_eye_apply_button, w.median_apply_button,
                              w.gaussian_apply_button, w.bilateral_apply_button,
                              w.mean_apply_button])

        pixmap = QPixmap("star_white.png")
        w.icon_label.setScaledContents(True)
        w.icon_label.setPixmap(pixmap)

        w.load_button.clicked.connect(lambda l: self.load_button_event(w.graphicsView))
        w.persmap_load_button.clicked.connect(lambda l: self.load_button_event(w.persmap_graphicsView))
        w.save_button.clicked.connect(lambda l: self.save_button_event())
        w.reset_button.clicked.connect(lambda l: self.reset_button_event("main_image"))
        w.persmap_reset_button.clicked.connect(lambda l: self.reset_button_event("persmap_image"))
        w.undo_button.clicked.connect(lambda l: self.undo_button_event())
        w.treeWidget.itemClicked.connect(self.dashboard_clicked_event)


        #w.graphicsView.mousePressEvent = self.getPos
        self.mouseFilter = MouseDetector()
        self.mouseFilter.app = self
        QApplication.instance().installEventFilter(self.mouseFilter)

        self.select_x_spinbox = None 
        self.select_y_spinbox = None 

        ######################### FISHEYE EFFECT CONTROLLERS #################################
        w.fisheye_x_spinbox.valueChanged.connect(lambda l: w.fisheye_x_slider.setValue(w.fisheye_x_spinbox.value()))
        w.fisheye_x_slider.valueChanged.connect(lambda l: w.fisheye_x_spinbox.setValue(w.fisheye_x_slider.value()))
        w.fisheye_x_spinbox.valueChanged.connect(lambda l: self.update_parameter("fisheye", "x", w.fisheye_x_spinbox.value()))

        w.fisheye_y_spinbox.valueChanged.connect(lambda l: w.fisheye_y_slider.setValue(w.fisheye_y_spinbox.value()))
        w.fisheye_y_slider.valueChanged.connect(lambda l: w.fisheye_y_spinbox.setValue(w.fisheye_y_slider.value()))
        w.fisheye_y_spinbox.valueChanged.connect(lambda l: self.update_parameter("fisheye", "y", w.fisheye_y_spinbox.value()))

        w.fisheye_sigma_spinbox.valueChanged.connect(lambda l: w.fisheye_sigma_slider.setValue(w.fisheye_sigma_spinbox.value()))
        w.fisheye_sigma_slider.valueChanged.connect(lambda l: w.fisheye_sigma_spinbox.setValue(w.fisheye_sigma_slider.value()))
        w.fisheye_sigma_spinbox.valueChanged.connect(lambda l: self.update_parameter("fisheye", "sigma", w.fisheye_sigma_spinbox.value()))

        ######################### SWIRL EFFECT CONTROLLERS ###################################
        w.swirl_x_spinbox.valueChanged.connect(lambda l: w.swirl_x_slider.setValue(w.swirl_x_spinbox.value()))
        w.swirl_x_slider.valueChanged.connect(lambda l: w.swirl_x_spinbox.setValue(w.swirl_x_slider.value()))
        w.swirl_x_spinbox.valueChanged.connect(lambda l: self.update_parameter("swirl", "x", w.swirl_x_spinbox.value()))

        w.swirl_y_spinbox.valueChanged.connect(lambda l: w.swirl_y_slider.setValue(w.swirl_y_spinbox.value()))
        w.swirl_y_slider.valueChanged.connect(lambda l: w.swirl_y_spinbox.setValue(w.swirl_y_slider.value()))
        w.swirl_y_spinbox.valueChanged.connect(lambda l: self.update_parameter("swirl", "y", w.swirl_y_spinbox.value()))

        w.swirl_sigma_spinbox.valueChanged.connect(lambda l: w.swirl_sigma_slider.setValue(w.swirl_sigma_spinbox.value()))
        w.swirl_sigma_slider.valueChanged.connect(lambda l: w.swirl_sigma_spinbox.setValue(w.swirl_sigma_slider.value()))
        w.swirl_sigma_spinbox.valueChanged.connect(lambda l: self.update_parameter("swirl", "sigma", w.swirl_sigma_spinbox.value()))

        w.swirl_magnitude_spinbox.valueChanged.connect(lambda l: w.swirl_magnitude_slider.setValue(w.swirl_magnitude_spinbox.value()))
        w.swirl_magnitude_slider.valueChanged.connect(lambda l: w.swirl_magnitude_spinbox.setValue(w.swirl_magnitude_slider.value()))
        w.swirl_magnitude_spinbox.valueChanged.connect(lambda l: self.update_parameter("swirl", "magnitude", w.swirl_magnitude_spinbox.value()))

        ######################### WAVES EFFECT CONTROLLERS ###################################
        w.waves_amplitude_spinbox.valueChanged.connect(lambda l: w.waves_amplitude_slider.setValue(w.waves_amplitude_spinbox.value()))
        w.waves_amplitude_slider.valueChanged.connect(lambda l: w.waves_amplitude_spinbox.setValue(w.waves_amplitude_slider.value()))
        w.waves_amplitude_spinbox.valueChanged.connect(lambda l: self.update_parameter("waves", "amplitude", w.waves_amplitude_spinbox.value()))

        w.waves_freq_spinbox.valueChanged.connect(lambda l: w.waves_freq_slider.setValue(w.waves_freq_spinbox.value()))
        w.waves_freq_slider.valueChanged.connect(lambda l: w.waves_freq_spinbox.setValue(w.waves_freq_slider.value()))
        w.waves_freq_spinbox.valueChanged.connect(lambda l: self.update_parameter("waves", "frequency", w.waves_freq_spinbox.value()))

        w.waves_phase_spinbox.valueChanged.connect(lambda l: w.waves_phase_slider.setValue(w.waves_phase_spinbox.value()))
        w.waves_phase_slider.valueChanged.connect(lambda l: w.waves_phase_spinbox.setValue(w.waves_phase_slider.value()))
        w.waves_phase_spinbox.valueChanged.connect(lambda l: self.update_parameter("waves", "phase", w.waves_phase_spinbox.value()))

        ######################### CYLINDER ANAMORPHOSIS CONTROLLERS ##########################
        w.cylinder_angle_spinbox.valueChanged.connect(lambda l: w.cylinder_angle_slider.setValue(w.cylinder_angle_spinbox.value()))
        w.cylinder_angle_slider.valueChanged.connect(lambda l: w.cylinder_angle_spinbox.setValue(w.cylinder_angle_slider.value()))
        w.cylinder_angle_spinbox.valueChanged.connect(lambda l: self.update_parameter("cylinder", "angle", w.cylinder_angle_spinbox.value()))

        ######################### RADIAL BLUR EFFECT CONTROLLERS #############################
        w.radial_sigma_spinbox.valueChanged.connect(lambda l: w.radial_sigma_slider.setValue(w.radial_sigma_spinbox.value()))
        w.radial_sigma_slider.valueChanged.connect(lambda l: w.radial_sigma_spinbox.setValue(w.radial_sigma_slider.value()))
        w.radial_sigma_spinbox.valueChanged.connect(lambda l: self.update_parameter("radial_blur", "sigma", w.radial_sigma_spinbox.value()))

        ######################### PERSPECTIVE MAPPING CONTROLLERS ############################
        w.persmap_x1_spinbox.valueChanged.connect(lambda l: self.update_parameter("pers_mapping", "x1", w.persmap_x1_spinbox.value()))
        w.persmap_y1_spinbox.valueChanged.connect(lambda l: self.update_parameter("pers_mapping", "y1", w.persmap_y1_spinbox.value()))
        w.persmap_x2_spinbox.valueChanged.connect(lambda l: self.update_parameter("pers_mapping", "x2", w.persmap_x2_spinbox.value()))
        w.persmap_y2_spinbox.valueChanged.connect(lambda l: self.update_parameter("pers_mapping", "y2", w.persmap_y2_spinbox.value()))
        w.persmap_x3_spinbox.valueChanged.connect(lambda l: self.update_parameter("pers_mapping", "x3", w.persmap_x3_spinbox.value()))
        w.persmap_y3_spinbox.valueChanged.connect(lambda l: self.update_parameter("pers_mapping", "y3", w.persmap_y3_spinbox.value()))
        w.persmap_x4_spinbox.valueChanged.connect(lambda l: self.update_parameter("pers_mapping", "x4", w.persmap_x4_spinbox.value()))
        w.persmap_y4_spinbox.valueChanged.connect(lambda l: self.update_parameter("pers_mapping", "y4", w.persmap_y4_spinbox.value()))

        w.persmap_select1_button.clicked.connect(lambda l: self.pers_mapping_select_button_event(w.persmap_x1_spinbox, w.persmap_y1_spinbox))
        w.persmap_select2_button.clicked.connect(lambda l: self.pers_mapping_select_button_event(w.persmap_x2_spinbox, w.persmap_y2_spinbox))
        w.persmap_select3_button.clicked.connect(lambda l: self.pers_mapping_select_button_event(w.persmap_x3_spinbox, w.persmap_y3_spinbox))
        w.persmap_select4_button.clicked.connect(lambda l: self.pers_mapping_select_button_event(w.persmap_x4_spinbox, w.persmap_y4_spinbox))

        ######################### SQUARE EYE EFFECT CONTROLLERS ##################################
        w.square_eye_x_spinbox.valueChanged.connect(lambda l: w.square_eye_x_slider.setValue(w.square_eye_x_spinbox.value()))
        w.square_eye_x_slider.valueChanged.connect(lambda l: w.square_eye_x_spinbox.setValue(w.square_eye_x_slider.value()))
        w.square_eye_x_spinbox.valueChanged.connect(lambda l: self.update_parameter("square_eye", "x", w.square_eye_x_spinbox.value()))

        w.square_eye_y_spinbox.valueChanged.connect(lambda l: w.square_eye_y_slider.setValue(w.square_eye_y_spinbox.value()))
        w.square_eye_y_slider.valueChanged.connect(lambda l: w.square_eye_y_spinbox.setValue(w.square_eye_y_slider.value()))
        w.square_eye_y_spinbox.valueChanged.connect(lambda l: self.update_parameter("square_eye", "y", w.square_eye_y_spinbox.value()))

        w.square_eye_sigma_spinbox.valueChanged.connect(lambda l: w.square_eye_sigma_slider.setValue(w.square_eye_sigma_spinbox.value()))
        w.square_eye_sigma_slider.valueChanged.connect(lambda l: w.square_eye_sigma_spinbox.setValue(w.square_eye_sigma_slider.value()))
        w.square_eye_sigma_spinbox.valueChanged.connect(lambda l: self.update_parameter("square_eye", "sigma", w.square_eye_sigma_spinbox.value()))

        w.square_eye_p_spinbox.valueChanged.connect(lambda l: w.square_eye_p_slider.setValue(w.square_eye_p_spinbox.value()))
        w.square_eye_p_slider.valueChanged.connect(lambda l: w.square_eye_p_spinbox.setValue(w.square_eye_p_slider.value()))
        w.square_eye_p_spinbox.valueChanged.connect(lambda l: self.update_parameter("square_eye", "p_value", w.square_eye_p_spinbox.value()))

        ######################### MEDIAN BLURRING CONTROLLERS ##################################
        w.median_size_spinbox.valueChanged.connect(lambda l: w.median_size_slider.setValue(w.median_size_spinbox.value()))
        w.median_size_slider.valueChanged.connect(lambda l: w.median_size_spinbox.setValue(w.median_size_slider.value()))
        w.median_size_spinbox.valueChanged.connect(lambda l: self.update_parameter("median", "size", w.median_size_spinbox.value()))

        ######################### GAUSSIAN FILTERING CONTROLLERS ##################################
        w.gaussian_radius_spinbox.valueChanged.connect(lambda l: w.gaussian_radius_slider.setValue(w.gaussian_radius_spinbox.value()))
        w.gaussian_radius_slider.valueChanged.connect(lambda l: w.gaussian_radius_spinbox.setValue(w.gaussian_radius_slider.value()))
        w.gaussian_radius_spinbox.valueChanged.connect(lambda l: self.update_parameter("gaussian", "radius", w.gaussian_radius_spinbox.value()))

        ######################### BILATERAL FILTER CONTROLLERS ##################################
        w.bilateral_sigma_spinbox.valueChanged.connect(lambda l: w.bilateral_sigma_slider.setValue(w.bilateral_sigma_spinbox.value()))
        w.bilateral_sigma_slider.valueChanged.connect(lambda l: w.bilateral_sigma_spinbox.setValue(w.bilateral_sigma_slider.value()))
        w.bilateral_sigma_spinbox.valueChanged.connect(lambda l: self.update_parameter("bilateral", "sigma", w.bilateral_sigma_spinbox.value()))

        w.bilateral_rho_spinbox.valueChanged.connect(lambda l: w.bilateral_rho_slider.setValue(w.bilateral_rho_spinbox.value()))
        w.bilateral_rho_slider.valueChanged.connect(lambda l: w.bilateral_rho_spinbox.setValue(w.bilateral_rho_slider.value()))
        w.bilateral_rho_spinbox.valueChanged.connect(lambda l: self.update_parameter("bilateral", "rho", w.bilateral_rho_spinbox.value()))

        ######################### MEAN FILTER CONTROLLERS ##################################
        w.mean_size_spinbox.valueChanged.connect(lambda l: w.mean_size_slider.setValue(w.mean_size_spinbox.value()))
        w.mean_size_slider.valueChanged.connect(lambda l: w.mean_size_spinbox.setValue(w.mean_size_slider.value()))
        w.mean_size_spinbox.valueChanged.connect(lambda l: self.update_parameter("mean", "size", w.mean_size_spinbox.value()))

        ######################### APPLY BUTTON CONTROLLERS ##################################
        w.fisheye_apply_button.clicked.connect(lambda l: self.fisheye_effect_apply_button_event())
        w.swirl_apply_button.clicked.connect(lambda l: self.swirl_effect_apply_button_event())
        w.waves_apply_button.clicked.connect(lambda l: self.waves_effect_apply_button_event())
        w.cylinder_apply_button.clicked.connect(lambda l: self.cylinder_effect_apply_button_event())
        w.radial_apply_button.clicked.connect(lambda l: self.radial_blur_effect_apply_button_event())
        w.persmap_apply_button.clicked.connect(lambda l: self.pers_mapping_apply_button_event())
        w.square_eye_apply_button.clicked.connect(lambda l: self.square_eye_apply_button_event())
        w.gaussian_apply_button.clicked.connect(lambda l: self.gaussian_blur_apply_button_event())
        w.median_apply_button.clicked.connect(lambda l: self.median_blur_apply_button_event())
        w.mean_apply_button.clicked.connect(lambda l: self.mean_blur_apply_button_event())
        w.bilateral_apply_button.clicked.connect(lambda l: self.bilateral_filter_apply_button_event())

    @Slot()
    def update_parameter(self, effect_name, parameter_name, value):
        self.parameters[effect_name][parameter_name] = value
        if self.image is not None:
            self.update_image(effect_name)
            print("update_image_function called")

    def update_image(self, effect_name):
        if effect_name=="fisheye":
            center_point = (self.parameters[effect_name]["y"],self.parameters[effect_name]["x"])
            sigma = self.parameters[effect_name]["sigma"]
            #output_image = model.fisheye_effect(self.image, center_point, sigma)
            self.worker.process(model.fisheye_effect, (self.image, center_point, sigma))

        elif effect_name=="swirl":
            center_point = (self.parameters[effect_name]["y"],self.parameters[effect_name]["x"])
            sigma = self.parameters[effect_name]["sigma"]
            magnitude = self.parameters[effect_name]["magnitude"]
            #output_image = model.swirl_effect(self.image, center_point, sigma, magnitude)
            self.worker.process(model.swirl_effect, (self.image, center_point, sigma, magnitude))

        elif effect_name=="waves":
            amplitude = [self.parameters[effect_name]["amplitude"], self.parameters[effect_name]["amplitude"]]
            frequency = [self.parameters[effect_name]["frequency"], self.parameters[effect_name]["frequency"]]
            phase = [self.parameters[effect_name]["phase"], self.parameters[effect_name]["phase"]]
            #output_image = model.waves_effect(self.image, amplitude, frequency, phase)
            self.worker.process(model.waves_effect, (self.image, amplitude, frequency, phase))

        elif effect_name=="cylinder":
            self.worker.process(model.cylinder, (self.image, self.parameters[effect_name]["angle"]))

        elif effect_name=="radial_blur":
            self.worker.process(model.radial_blur_effect, (self.image, self.parameters[effect_name]["sigma"]))
            #output_image = model.radial_blur_effect(self.image, sigma=self.parameters[effect_name]["sigma"])

        elif effect_name=="pers_mapping":
            if self.persmap_image is not None:
                u_ul = (self.parameters[effect_name]["x1"], self.parameters[effect_name]["y1"])
                u_ur = (self.parameters[effect_name]["x2"], self.parameters[effect_name]["y2"])
                u_ll = (self.parameters[effect_name]["x3"], self.parameters[effect_name]["y3"])
                u_lr = (self.parameters[effect_name]["x4"], self.parameters[effect_name]["y4"])
                self.worker.process(model.perspective_mapping, (self.persmap_image, self.image, u_ul, u_ur, u_ll, u_lr), split_dimensions=False)

        elif effect_name=="square_eye":
            center_point = (self.parameters[effect_name]["y"],self.parameters[effect_name]["x"])
            sigma = self.parameters[effect_name]["sigma"]
            p_value = self.parameters[effect_name]["p_value"]
            #output_image = model.square_eye_effect(self.image, center_point, sigma, p_value)
            self.worker.process(model.square_eye_effect, (self.image, center_point, sigma, p_value))

        elif effect_name=="median":
            self.worker.process(model.median_filter, (self.image, self.parameters[effect_name]["size"]))

        elif effect_name=="gaussian":
            self.worker.process(model.gaussian_filter, (self.image, self.parameters[effect_name]["radius"]))

        elif effect_name=="bilateral":
            sigma = self.parameters[effect_name]["sigma"]
            rho = self.parameters[effect_name]["rho"]
            self.worker.process(model.bilateral_filter, (self.image, sigma, rho))

        elif effect_name=="mean":
            self.worker.process(model.mean_filter, (self.image, self.parameters[effect_name]["size"]))


    # For threading
    @Slot(object)
    def update_image_view(self, output_image):
        self.preview_image = output_image.copy()

        if np.issubdtype(output_image.dtype, np.floating):
            output_image = (output_image*255).astype(np.uint8)

        view_image = ImageQt.ImageQt( Image.fromarray(output_image) ) # convert output_image to qimage
        pixmap = QPixmap.fromImage(view_image)
        self.scene = QGraphicsScene()
        self.scene.addPixmap(pixmap)
        self.window.graphicsView.setScene(self.scene)
        item = self.window.graphicsView.items()
        self.window.graphicsView.fitInView(item[0],Qt.KeepAspectRatio)

    def get_default_parameters(self):
        parameters = {"fisheye": {"x": 0, "y": 0, "sigma": 1.0}, 
                      "swirl": {"x": 0, "y": 0, "sigma": 0.1, "magnitude":0},
                      "waves": {"amplitude": 0.1, "frequency": 0.1, "phase": 0},
                      "cylinder": {"angle": 0.0},
                      "radial_blur": {"sigma": 0.1},
                      "pers_mapping": {"x1":0, "y1":0, "x2":0, "y2":0, "x3":0, "y3":0, "x4":0, "y4":0},
                      "square_eye": {"x": 0, "y": 0, "sigma": 1.0, "p_value":0.1},
                      "median": {"size": 3.0},
                      "gaussian": {"radius": 2.0},
                      "bilateral": {"sigma": 100, "rho": 50},
                      "mean": {"size": 3.0},}
        return parameters

    # disable buttons and input widgets
    def disable_buttons(self, buttons):
        for button in buttons:
            button.setEnabled(False)

    # enable buttons and input widgets
    def enable_buttons(self, buttons):
        for button in buttons:
            button.setEnabled(True)

    def set_parameter_limits(self):
        print("Set max min limits of slider and spinbox")

        w = self.window
        self.set_limits([w.fisheye_x_slider, w.fisheye_y_slider, w.fisheye_sigma_slider,
                         w.swirl_x_slider, w.swirl_y_slider, w.swirl_sigma_slider, w.swirl_magnitude_slider,
                         w.waves_amplitude_slider, w.waves_freq_slider, w.waves_phase_slider,
                         w.cylinder_angle_slider,
                         w.radial_sigma_slider, 
                         w.square_eye_x_slider, w.square_eye_y_slider, w.square_eye_sigma_slider, w.square_eye_p_slider], "slider")

        self.set_limits([w.fisheye_x_spinbox, w.fisheye_y_spinbox, w.fisheye_sigma_spinbox,
                         w.swirl_x_spinbox, w.swirl_y_spinbox, w.swirl_sigma_spinbox,w.swirl_magnitude_spinbox,
                         w.waves_amplitude_spinbox, w.waves_freq_spinbox, w.waves_phase_spinbox,
                         w.cylinder_angle_spinbox,
                         w.radial_sigma_spinbox,
                         w.square_eye_x_spinbox, w.square_eye_y_spinbox, w.square_eye_sigma_spinbox, w.square_eye_p_spinbox,
                         w.persmap_x1_spinbox, w.persmap_y1_spinbox, w.persmap_x2_spinbox, w.persmap_y2_spinbox,
                         w.persmap_x3_spinbox, w.persmap_y3_spinbox, w.persmap_x4_spinbox, w.persmap_y4_spinbox])

    def set_limits(self, input_widgets, kind=None):
        max_x, max_y = self.image.shape[1], self.image.shape[0]

        for widget in input_widgets:
            #print(widget.accessibleName())
            widget.setMinimum(0)
            if kind == "slider":
                widget.setTickInterval(1)

            if widget.accessibleName() == "x":
                widget.setMaximum(max_x)
            elif widget.accessibleName() == "y":
                widget.setMaximum(max_y)
            elif widget.accessibleName() == "amplitude" or widget.accessibleName()=="frequency" or widget.accessibleName()=="swirl_sigma" or widget.accessibleName()=="radial_sigma" or widget.accessibleName()=="p_value":
                widget.setMinimum(0.1)
            elif widget.accessibleName() == "cylinder_angle":
                widget.setMaximum(360.0)
            elif widget.accessibleName()=="fisheye_sigma" or widget.accessibleName()=="squareeye_sigma":
                widget.setMinimum(1.0)
                widget.setMaximum(500.0)
                if kind == "slider":
                    widget.setTickInterval(5)
                else:
                    widget.setSingleStep(5)

    @Slot()
    def load_button_event(self, graphicsView):
        w = self.window
        self.image_file_name = QFileDialog.getOpenFileName(self.window, "Open Image", ".", "Image Files (*.png *.jpg *.bmp)")
        
        if self.image_file_name[0] != "":

            reader = QImageReader(self.image_file_name[0])
            reader.setAutoTransform(True)
            new_image = reader.read()
            if (new_image.isNull()):
                print("Image not found")

            self.scene = QGraphicsScene()
            pixmap = QPixmap.fromImage(new_image)

            self.scene.addPixmap(pixmap)
            graphicsView.setScene(self.scene)
            item = graphicsView.items()
            graphicsView.fitInView(item[0],Qt.KeepAspectRatio)

            if graphicsView.accessibleName()=="graphicsView":
                #self.image = self.image_read(self.image_file_name[0], pilmode="RGB") / 255.0
                self.image = Image.open(self.image_file_name[0])
                self.image = np.array(self.image) / 255.0
                self.images_stack.append(("original image",self.image))
                #plt.imshow(self.image, cmap="gray")
                #plt.show()
                print(self.image.shape)

                # enable the buttons that were disabled in the beginning
                self.enable_buttons([w.save_button, w.reset_button,
                                     w.fisheye_apply_button, w.swirl_apply_button,
                                     w.waves_apply_button, w.cylinder_apply_button,
                                     w.radial_apply_button,
                                     w.square_eye_apply_button,
                                     w.gaussian_apply_button, w.median_apply_button,
                                     w.mean_apply_button, w.bilateral_apply_button])

                self.set_parameter_limits()

            elif graphicsView.accessibleName()=="persmap_graphicsView":
                print("girdi")
                self.persmap_image = Image.open(self.image_file_name[0])
                self.persmap_image = np.array(self.persmap_image) / 255.0
                self.enable_buttons([w.persmap_apply_button])


    @Slot()
    def save_button_event(self):
        file_name_to_save = QFileDialog.getSaveFileName(self.window, "Open Image", ".", "Image Files (*.png *.jpg *.bmp)")[0]

        extension_list = ["png", "jpg", "jpeg"]
        if any(substring in file_name_to_save for substring in extension_list) == False:
            file_name_to_save = file_name_to_save + ".png"

        image_to_be_saved = self.image.copy()
        if np.issubdtype(image_to_be_saved.dtype, np.floating):
            image_to_be_saved = (self.image*255).astype(np.uint8)

        self.image_write(image_to_be_saved, file_name_to_save)

    @Slot()
    def reset_button_event(self, image="main_image"):
        if image=="main_image":
            self.window.graphicsView.setScene(None)
            self.image = None
            self.disable_buttons([self.window.save_button, self.window.reset_button, self.window.undo_button,
                                  self.window.fisheye_apply_button, self.window.swirl_apply_button,
                                  self.window.waves_apply_button, self.window.cylinder_apply_button,
                                  self.window.radial_apply_button, self.window.persmap_apply_button,
                                  self.window.square_eye_apply_button, self.window.gaussian_apply_button,
                                  self.window.median_apply_button, self.window.mean_apply_button,
                                  self.window.bilateral_apply_button])
        elif image=="persmap_image":
            self.window.persmap_graphicsView.setScene(None)
            self.persmap_image = None
            self.window.persmap_apply_button.setEnabled(False)

        print("reseted")

    @Slot()
    def undo_button_event(self):
        if len(self.images_stack)>1:
            self.images_stack.pop()
            self.image = self.images_stack[-1][1].copy()
            view_image = self.images_stack[-1][1].copy()  # To view image on the GraphicView

            if np.issubdtype(view_image.dtype, np.floating):
                view_image = (view_image*255).astype(np.uint8)

            view_image = ImageQt.ImageQt( Image.fromarray(view_image) ) # convert view_image to qimage
            pixmap = QPixmap.fromImage(view_image)
            self.scene = QGraphicsScene()
            self.scene.addPixmap(pixmap)
            self.window.graphicsView.setScene(self.scene)
            item = self.window.graphicsView.items()
            self.window.graphicsView.fitInView(item[0],Qt.KeepAspectRatio)

            print("----------------------->",len(self.images_stack))
            if len(self.images_stack)==1:
                self.disable_buttons([self.window.undo_button])


    @Slot()
    def dashboard_clicked_event(self, position, column):
        # get item name from the tree on the left bar
        item_name = position.text(column)
        if item_name in self.effects_to_tab_idx:
            self.window.tabWidget.setCurrentIndex(self.effects_to_tab_idx[item_name])
            self.current_tab_idx = self.effects_to_tab_idx[item_name]
            self.current_tab_name = item_name
            # enables the buttons and parameters if the effect is revisited after applying
            if self.image is not None:
                self.tabs_to_apply_buttons_and_params[item_name]["button"].setEnabled(True)
                for widget in self.tabs_to_apply_buttons_and_params[item_name]["params"]:
                    widget.setEnabled(True)
            if self.persmap_image is None:
                self.tabs_to_apply_buttons_and_params["Perspective Mapping"]["button"].setEnabled(False)

    @Slot()
    def fisheye_effect_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("fish eye effect", self.image))  # added to the stack
        print(self.images_stack)

        for widget in self.fisheye_effect_parameters:
            widget.setEnabled(False)
        self.window.fisheye_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def swirl_effect_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("swirl effect", self.image))  # added to the stack
        print(self.images_stack)

        for widget in self.swirl_effect_parameters:
            widget.setEnabled(False)
        self.window.swirl_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def waves_effect_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("waves effect", self.image))  # added to the stack
        print(self.images_stack)

        for widget in self.waves_effect_parameters:
            widget.setEnabled(False)
        self.window.waves_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def cylinder_effect_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("cylinder effect", self.image))  # added to the stack
        print(self.images_stack)

        for widget in self.cylinder_effect_parameters:
            widget.setEnabled(False)
        self.window.cylinder_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def radial_blur_effect_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("radial blur effect", self.image))  # added to the stack
        print(self.images_stack)

        for widget in self.radial_blur_effect_parameters:
            widget.setEnabled(False)
        self.window.radial_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def pers_mapping_select_button_event(self, x, y):
        self.select_x_spinbox = x
        self.select_y_spinbox = y

    @Slot()
    def pers_mapping_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("pers mapping effect", self.image))  # added to the stack
        print(self.images_stack)

        for widget in self.pers_mapping_parameters:
            widget.setEnabled(False)
        self.window.persmap_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def square_eye_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("square eye effect", self.image))  # added to the stack
        print(self.images_stack)

        for widget in self.square_eye_effect_parameters:
            widget.setEnabled(False)
        self.window.square_eye_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def gaussian_blur_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("gaussian blur effect", self.image))  # added to the stack
        print(self.images_stack)

        for widget in self.gaussian_blur_parameters:
            widget.setEnabled(False)
        self.window.gaussian_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def median_blur_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("median blur effect", self.image))  # added to the stack
        print(self.images_stack)

        for widget in self.median_blur_parameters:
            widget.setEnabled(False)
        self.window.median_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def mean_blur_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("mean blur effect", self.image))  # added to the stack
        print(self.images_stack)

        for widget in self.mean_blur_parameters:
            widget.setEnabled(False)
        self.window.mean_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def bilateral_filter_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("bilateral filter effect", self.image))  # added to the stack
        print(self.images_stack)

        for widget in self.gaussian_blur_parameters:
            widget.setEnabled(False)
        self.window.gaussian_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)


    def image_read(self, file_name, pilmode='RGB', arrtype=np.float):
        """
        pilmode: str
            for luminance / intesity images use 'L'
            for RGB color images use 'RGB'
        arrtype: numpy dtype
            use np.float, np.uint8, ...
        """
        return imageio.imread(file_name, pilmode=pilmode).astype(arrtype)

    def image_write(self, image, file_name, arrtype=np.uint8):
        print(image.dtype)
        imageio.imwrite(file_name, np.array(image).astype(arrtype))


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    my_app = MyApplication()

    with open("style.qss", "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    app.exec()