import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QSlider
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
import cv2
import os


class VideoFrameExtractor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Video Frame Extractor")
        self.setGeometry(100, 100, 800, 600)

        self.video_path = None
        self.capture = None
        self.current_frame_index = 0
        self.total_frames = 0
        self.output_dir = "frames"
        self.max_width = 1024
        self.max_height = 768
        self.aspect_ratio = 16 / 9

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel(self)
        self.label.setStyleSheet("QLabel { background-color : black; }")
        layout.addWidget(self.label)

        self.import_button = QPushButton("Import Video", self)
        self.import_button.clicked.connect(self.import_video)
        layout.addWidget(self.import_button)

        # Controls Layout (Previous Frame, Next Frame, Export Frame)
        controls_layout = QHBoxLayout()

        self.prev_button = QPushButton("Previous Frame (or Left Arrow Key)", self)
        self.prev_button.clicked.connect(self.prev_frame)
        self.prev_button.setEnabled(False)
        controls_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next Frame (or Right Arrow Key)", self)
        self.next_button.clicked.connect(self.next_frame)
        self.next_button.setEnabled(False)
        controls_layout.addWidget(self.next_button)

        self.export_button = QPushButton("Export Frame", self)
        self.export_button.clicked.connect(self.export_frame)
        self.export_button.setEnabled(False)
        controls_layout.addWidget(self.export_button)

        layout.addLayout(controls_layout)

        # Slider Layout (Pause Button and Video Slider)
        slider_layout = QHBoxLayout()

        self.pause_button = QPushButton("Pause", self)
        self.pause_button.clicked.connect(self.pause_video)
        slider_layout.addWidget(self.pause_button)

        self.video_slider = QSlider(Qt.Horizontal, self)
        self.video_slider.setRange(0, 100)
        self.video_slider.sliderMoved.connect(self.slider_moved)
        slider_layout.addWidget(self.video_slider)

        layout.addLayout(slider_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_slider)

    def import_video(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        self.video_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)",
                                                         options=options)

        if self.video_path:
            self.capture = cv2.VideoCapture(self.video_path)

            if self.capture.isOpened():
                self.total_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
                self.current_frame_index = 0
                self.show_frame()
                self.prev_button.setEnabled(True)
                self.next_button.setEnabled(True)
                self.export_button.setEnabled(True)
                self.video_slider.setRange(0, self.total_frames - 1)
                self.timer.start(int(1000 / 30))
            else:
                self.label.setText("Failed to open the video.")

    def show_frame(self):
        if self.capture and self.capture.isOpened():
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_index)
            success, frame = self.capture.read()
            if success:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)

                scale_width = self.max_width / w
                scale_height = self.max_height / h
                scale_factor = min(scale_width, scale_height)

                new_width = int(w * scale_factor)
                new_height = int(h * scale_factor)

                result_frame = cv2.resize(frame_rgb, (new_width, new_height))

                top_bottom_margin = (self.max_height - new_height) // 2
                left_right_margin = (self.max_width - new_width) // 2

                final_frame = cv2.copyMakeBorder(result_frame, top_bottom_margin, top_bottom_margin,
                                                 left_right_margin, left_right_margin, cv2.BORDER_CONSTANT, value=(0, 0, 0))

                final_qt_image = QImage(final_frame.data, final_frame.shape[1], final_frame.shape[0],
                                        final_frame.strides[0], QImage.Format_RGB888)
                final_pixmap = QPixmap.fromImage(final_qt_image)
                self.label.setPixmap(final_pixmap)

                self.setFixedSize(self.max_width, self.max_height + 100)
            else:
                self.label.setText("Failed to load frame.")

    def prev_frame(self):
        if self.current_frame_index > 0:
            self.current_frame_index -= 1
            self.show_frame()

    def next_frame(self):
        if self.current_frame_index < self.total_frames - 1:
            self.current_frame_index += 1
            self.show_frame()

    def export_frame(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_index)
        success, frame = self.capture.read()

        if success:
            frame_path = os.path.join(self.output_dir, f"frame_{self.current_frame_index:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            self.label.setText(f"Frame {self.current_frame_index} exported to '{frame_path}'")
        else:
            self.label.setText("Failed to export frame.")

    def slider_moved(self):
        self.current_frame_index = self.video_slider.value()
        self.show_frame()

    def update_slider(self):
        if self.capture and self.capture.isOpened():
            self.video_slider.setValue(self.current_frame_index)
            self.current_frame_index += 1
            if self.current_frame_index >= self.total_frames:
                self.timer.stop()
            self.show_frame()

    def pause_video(self):
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("Resume")
        else:
            self.timer.start(int(1000 / 30))
            self.pause_button.setText("Pause")

    def keyPressEvent(self, event):
        if event.key() == 16777234:
            self.prev_frame()
        elif event.key() == 16777236:
            self.next_frame()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoFrameExtractor()
    window.show()
    sys.exit(app.exec_())
