import sys
from PyQt5.QtWidgets import(QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton,
        QHBoxLayout, QTextEdit)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import pyqtgraph as pg
import asyncio
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from bleak import BleakScanner 
from bleak.backends.scanner import AdvertisementData  

class BluetoothScannerThread(QThread):
    # emits a dict: address → (BLEDevice, AdvertisementData)
    devices_found = pyqtSignal(dict)

    def run(self):
        # 1. Create a brand-new loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # 2. Run our manual scanner coroutine
            devices = loop.run_until_complete(self._scan_once(timeout=3.0))
            self.devices_found.emit(devices)
        except Exception as e:
            print("Scanner thread error:", e)
        finally:
            # 3. Cleanly close the loop so no callbacks are left dangling
            loop.close()

    async def _scan_once(self, timeout: float) -> dict[str, tuple]:
        """
        Perform a single scan by manually start/stop’ing the scanner.
        Returns a dict[address] = (BLEDevice, AdvertisementData)
        """
        result: dict[str, tuple] = {}

        # callback builds our result map
        def _cb(device, adv: AdvertisementData):
            result[device.address] = (device, adv)

        scanner = BleakScanner(detection_callback=_cb, return_adv=True)
        try:
            await scanner.start()
            await asyncio.sleep(timeout)
            await scanner.stop()

            # ✅ Give WinRT backend some time to finish callbacks before loop closes
            await asyncio.sleep(0.1)
        except Exception as e:
            print("Scan error:", e)

        return result

class BluetoothRSSIApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bluetooth RSSI Monitor")
        self.resize(800, 600)

        self.device_data = {}  # {name: [RSSI values]}
        self.curves = {}
        self.max_points = 100
        self.selected_device = None
        self.trigger_state = False
        self.device_rssi, self.device_rssi_2, self.device_rssi_3 = 0,0,0

        self.combo_state, self.combo_state2, self.combo_state3 = True,True,True

        self.init_ui()
        self.setup_timer()
        self._connect_signals()

    def init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        btn_layout = QHBoxLayout()
        self.trigger_btn   = QPushButton("Start Recording")
        self.clear_btn   = QPushButton("Clear")
        btn_layout.addWidget(self.trigger_btn)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)

        combo_layout = QHBoxLayout()
        self.combo_box = QComboBox()
        self.combo_box.currentTextChanged.connect(self.select_device)
        self.combo_box.setStyleSheet("color: red")
        self.combo_btn   = QPushButton("1|0")
        combo_layout.addWidget(self.combo_box, stretch=3)
        combo_layout.addWidget(self.combo_btn, stretch=1)
        layout.addLayout(combo_layout)

        combo2_layout = QHBoxLayout()
        self.combo_box2 = QComboBox()
        self.combo_box2.currentTextChanged.connect(self.select_device2)
        self.combo_box2.setStyleSheet("color: green")
        self.combo_btn2   = QPushButton("1|0")
        combo2_layout.addWidget(self.combo_box2, stretch=3)
        combo2_layout.addWidget(self.combo_btn2, stretch=1)
        layout.addLayout(combo2_layout)

        combo3_layout = QHBoxLayout()
        self.combo_box3 = QComboBox()
        self.combo_box3.currentTextChanged.connect(self.select_device3)
        self.combo_box3.setStyleSheet("color: blue")
        self.combo_btn3   = QPushButton("1|0")
        combo3_layout.addWidget(self.combo_box3, stretch=3)
        combo3_layout.addWidget(self.combo_btn3, stretch=1)
        layout.addLayout(combo3_layout)

        self.text_widget  = QTextEdit(readOnly=True)
        self.text_widget.setFont(QFont("Arial", 12))
        layout.addWidget(self.text_widget, stretch=1)

        self.plot_widget = pg.PlotWidget(title="Bluetooth RSSI")
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel("left", "RSSI (dBm)")
        self.plot_widget.setLabel("bottom", "Time (samples)")
        self.plot_widget.showGrid(x=True, y=True)
        layout.addWidget(self.plot_widget, stretch=2)

        self.setCentralWidget(central_widget)

    def append_text(self, text):
        self.text_widget.append(text)
        # Auto-scroll to the latest line
        scrollbar = self.text_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        line_count = self.text_widget.document().blockCount()
        if line_count > 100:  # Clear if lines exceed 100
            self.text_widget.clear()
    
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.scan_devices)
        self.timer.start(1000)

    def select_device(self, name):
        self.selected_device = name

    def select_device2(self, name):
        self.selected_device2 = name

    def select_device3(self, name):
        self.selected_device3 = name

    def scan_devices(self):
        self.scanner_thread = BluetoothScannerThread()
        self.scanner_thread.devices_found.connect(self.handle_devices)
        self.scanner_thread.start()

    def handle_devices(self, devices: dict):
        # for d in devices:
        #     name = d.name or d.address
        #     if name not in self.device_data:
        #         self.device_data[name] = []
        #         self.combo_box.addItem(name)
        #         self.curves[name] = self.plot_widget.plot(pen=pg.mkPen(width=1))

        #     self.device_data[name].append(d.rssi)
        #     if len(self.device_data[name]) > self.max_points:
        #         self.device_data[name] = self.device_data[name][-self.max_points:]

        for address, (device, adv) in devices.items():
            name = device.name or device.address
            if name not in self.device_data:
                self.combo_box.addItem(name)
                self.combo_box2.addItem(name)
                self.combo_box3.addItem(name)
                self.curves[name] = self.plot_widget.plot(pen=pg.mkPen(width=1))
                self.device_data[name] = [float('nan')] * (len(next(iter(self.device_data.values()), [])))

        if self.trigger_state:
            for name in self.device_data:
                self.device_data[name].append(float('nan'))

            # Then update RSSI only for devices found
            for address, (device, adv) in devices.items():
                name = device.name or address
                if len(self.device_data[name]) > 0:
                    self.device_data[name][-1] = adv.rssi  # Replace the NaN with actual RSSI

            # Keep lists to max_points
            for name in self.device_data:
                if len(self.device_data[name]) > self.max_points:
                    self.device_data[name] = self.device_data[name][-self.max_points:]

            self.update_plot()

    def update_plot(self):
        for name, rssi_list in self.device_data.items():
            x = list(range(len(rssi_list)))
            # pen = pg.mkPen(width=3 if name == self.selected_device else 1)
            if name == self.selected_device and self.combo_state:
                pen=pg.mkPen(pg.mkColor(255, 0, 0, 255), width=3)
                if not np.isnan(rssi_list[-1]):
                    self.device_rssi = rssi_list[-1]
                # print("1:", self.device_rssi)
            elif name == self.selected_device2 and self.combo_state2:
                pen=pg.mkPen(pg.mkColor(0, 255, 0, 255), width=3)
                if not np.isnan(rssi_list[-1]):
                    self.device_rssi_2 = rssi_list[-1]
                # print("2:", self.device_rssi_2)
            elif name == self.selected_device3 and self.combo_state3:
                pen=pg.mkPen(pg.mkColor(0, 0, 255, 255), width=3)
                if not np.isnan(rssi_list[-1]):
                    self.device_rssi_3 = rssi_list[-1]
                # print("2:", self.device_rssi_2)
            else:
                pen=pg.mkPen(pg.mkColor(100, 100, 200, 50), width=1)
            self.curves[name].setPen(pen)
            self.curves[name].setData(x, rssi_list)

        try:
            self.append_text(f"RSSI({self.device_rssi}, {self.device_rssi_2}, {self.device_rssi_3}),   diff({self.device_rssi-self.device_rssi_2}, {self.device_rssi_2-self.device_rssi_3})")
        except:
            print("Text window ERROR")
    
    def trigger(self):
        self.trigger_state = not self.trigger_state
        if self.trigger_state == True:
            self.trigger_btn.setText("Stop Recording...")
        else:
            self.trigger_btn.setText("Start Recording")


    def clear(self):
        self.device_data = {}  # {name: [RSSI values]}
        self.curves = {}
        self.plot_widget.clear()
        self.text_widget.clear()

    def combo(self):
        self.combo_state = not self.combo_state
        self.combo_box.setEnabled(self.combo_state)
    def combo2(self):
        self.combo_state2 = not self.combo_state2
        self.combo_box2.setEnabled(self.combo_state2)
    def combo3(self):
        self.combo_state3 = not self.combo_state3
        self.combo_box3.setEnabled(self.combo_state3)

    def _connect_signals(self):
        self.trigger_btn.clicked.connect(self.trigger)
        self.clear_btn.clicked.connect(self.clear)
        self.combo_btn.clicked.connect(self.combo)
        self.combo_btn2.clicked.connect(self.combo2)
        self.combo_btn3.clicked.connect(self.combo3)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BluetoothRSSIApp()
    window.show()
    sys.exit(app.exec_())
