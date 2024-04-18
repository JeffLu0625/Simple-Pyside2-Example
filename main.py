
import os
import sys

from ui_interface import *
from Custom_Widgets.Widgets import *
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import numpy as np
import time
import threading
import cv2

settings = QSettings()

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        loadJsonStyle(self, self.ui)
        self.initializeStatusBar()
        # Link scene and graphicsView
        self.graphics_scene = QGraphicsScene()
        self.ui.graphicsView.setScene(self.graphics_scene)
        # Set up parameters
        self.side = [100,200]
        # self.data = cv2.imread('water.png', cv2.IMREAD_GRAYSCALE)
        self.data = cv2.imread(sys.argv[1])
        # self.result = self.ProcessImage()
        self.data = cv2.cvtColor(self.data, cv2.COLOR_BGR2RGB)
        # self.result = cv2.resize(self.result, (750, 500), interpolation=cv2.INTER_AREA)
        self.array_size = self.data.shape[:2]
        # self.array_size = (500,700)
        # self.data = np.random.rand(*self.array_size)
        # self.data[self.side[0]:self.array_size[0]-self.side[0],self.side[1]:self.array_size[1]-self.side[1]] = 1.5
        self.start = 0
        self.numFrame = 1
        self.moving = False
        self.plot_thread = None
        # Initialize plot
        self.initializePlot()

        # Callbacks
        self.ui.pushButton_2.clicked.connect(self.StartButtonClicked)
        self.ui.pushButton_3.clicked.connect(self.StopButtonClicked)
        
        self.show()
        self.resizePlot() 

    def StartButtonClicked(self):
        if not self.plot_thread or not self.plot_thread.is_alive():
            self.plot_thread = threading.Thread(target=self.Plot)  # Use self.Plot
            self.plot_thread.start()
            self.ui.pushButton_2.setEnabled(False)
            self.ui.pushButton_3.setEnabled(True)

    def StopButtonClicked(self, event):
        self.moving = False
        if self.plot_thread and self.plot_thread.is_alive():
            self.label1.setText("Stopped manually")
            self.ui.pushButton_2.setEnabled(True)
            self.ui.pushButton_3.setEnabled(False)

    def initializeStatusBar(self):
        self.label1 = QLabel("Idel")
        self.label1.setStyleSheet('border: 0')
        self.label2 = QLabel("frame #: ")
        self.label2.setStyleSheet('border: 0')
        self.label3 = QLabel("fps: ")
        self.label3.setStyleSheet('border: 0')
        self.statusBar().addPermanentWidget(self.label1, stretch=3)
        self.statusBar().addPermanentWidget(self.label2, stretch=3)
        self.statusBar().addPermanentWidget(self.label3, stretch=3)
        

    def initializePlot(self):
        self.fig = Figure()
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.ax = self.fig.add_axes([0.0, 0.0, 1.0, 1.0])
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)
        
        # self.ax.imshow(self.data, cmap='gray', interpolation='nearest', origin='lower', aspect='auto')
        # resized_data = cv2.resize(self.data, (750, 500), interpolation=cv2.INTER_AREA)
        self.ax.imshow(self.data, interpolation='nearest', origin='lower', aspect='auto')
        
        # Add the Matplotlib canvas to the QGraphicsScene
        self.graphics_scene.addWidget(self.canvas)
        self.canvas.draw()
        # self.ui.graphicsView.resize(self.array_size[0], self.array_size[1])
        # self.ui.graphicsView.show()
        # self.resizePlot()

    def resizePlot(self):
        self.ui.graphicsView.fitInView(self.graphics_scene.sceneRect())

    def Plot(self):
         self.moving = True
         cumulate_time = 0
         self.start = 0
         self.numFrame = 1
         t1 = time.time()
         step = 2
         self.label1.setText("Running")
        #  self.resizePlot()
         while self.moving:
            if self.start >= 2*self.array_size[1]:
                self.start = 0
            show_array = np.zeros_like(self.data)
            if self.start <= self.array_size[1]:
                show_array[:,:self.start,:] = self.data[:, self.array_size[1] - self.start:self.array_size[1], :]
            else:
                gap = self.start - self.array_size[1]
                show_array[:,gap:self.array_size[1],:] = self.data[:, :self.array_size[1] - gap, :]
            result = self.ProcessImage(show_array)
            self.updatePlot(result)
            t2 = time.time()
            self.label2.setText(f"frame #{self.numFrame}")
            cumulate_time = t2 - t1
            if cumulate_time > 0:
                fps = self.numFrame / cumulate_time
                self.label3.setText(f"{fps:.2f} fps")
            self.start += step
            self.numFrame += 1

    def updatePlot(self, array):
        self.ax.clear()
        # self.ax.imshow(array, interpolation='nearest', origin='lower', aspect='auto', extent=[0,array.shape[0],0,array.shape[1]])
        # resized_data = cv2.resize(array, (750, 500), interpolation=cv2.INTER_AREA)
        self.ax.imshow(array, interpolation='nearest', origin='lower', aspect='auto')
        self.canvas.draw()

    def ProcessImage(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        
        # Define the color range for the background (red)
        lower_red = np.array([0, 255, 255]) # [0, 50, 50]
        upper_red = np.array([10, 255, 255])

        # Create a mask based on the color range
        mask = cv2.inRange(hsv, lower_red, upper_red)
        counter_mask = mask.copy()
        counter_mask[counter_mask==0]  = 1
        counter_mask[counter_mask==255] = 0
        counter_mask[counter_mask==1] = 255

        blur = cv2.GaussianBlur(counter_mask, (7,7), 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20,20)) # MORPH_RECT MORPH_ELLIPSE
        open = cv2.morphologyEx(blur, cv2.MORPH_OPEN, kernel)
        open = cv2.GaussianBlur(open, (3,3), 0)

        # Threshold the image
        final_mask = np.ones_like(mask) * 255
        final_mask[open > 130] = 0

        # Apply the mask to the original image
        result = cv2.bitwise_and(img, img, mask=final_mask)

        # Replace the black background with red
        result_gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        result_rgb = cv2.cvtColor(result_gray, cv2.COLOR_GRAY2RGB)
        result_final = self.ReplaceColorWithRed(result_rgb, [0,0,0])
        
        # Detect regions
        black_boxes = self.find_black_regions(result.copy())
        self.draw_rectangles(img, black_boxes)
        
        return img

    def ReplaceColorWithRed(self, img, color):
        mask = np.all(img == color, axis=-1)
        # Create a red replacement Image
        red_replacement = np.zeros_like(img)
        red_replacement[:, :, 0] = 255  # Set the red channel to maximum
        # Replace masked regions with red
        result = img.copy() 
        result[mask] = red_replacement[mask]
        return result
    
    def find_black_regions(self, image, threshold=1):
        # Convert the image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold the grayscale image to create a binary mask
        #   _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)[1]
        # Add edge detction to amplify the black regions at edges
        edges = cv2.Canny(mask, 100, 200)
        
        # Find contours in the mask
        contours, _ = cv2.findContours(edges, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        # Find bounding boxes for the contours
        black_boxes = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w*h > 500:
                black_boxes.append((x, y, x + w, y + h))

        return black_boxes

    def draw_rectangles(self, image, black_boxes):
        """
        Draws rectangles around the black regions on the image.

        Args:
            image: The input image as a NumPy array.
            black_boxes: A list of bounding boxes (x_min, y_min, x_max, y_max) for the black regions.
        """
        for x, y, x_max, y_max in black_boxes:
            # Draw a green rectangle around the black region
            cv2.rectangle(image, (x, y), (x_max, y_max), (0, 0, 255), 2)
        
########################################################################
## EXECUTE APP
########################################################################
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ########################################################################
    ## 
    ########################################################################
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
########################################################################
## END===>
########################################################################  
