![Bluetooth RSSI Monitor PyQT5](https://github.com/user-attachments/assets/bbdd698e-92d3-43ba-805a-0b77bcd88e31)

# 🔍 Bluetooth RSSI Monitor (PyQt5 + Bleak + PyQtGraph)

A desktop application built with **PyQt5**, **Bleak**, and **PyQtGraph** that scans for nearby Bluetooth Low Energy (BLE) devices, monitors their **RSSI (signal strength)** in real time, and displays the data in a dynamic line graph.

## 🧠 Features

- Real-time Bluetooth LE device scanning (using `bleak`)
- Displays RSSI data as scrolling line plots (with `pyqtgraph`)
- Select and highlight a specific device by name
- Supports multiple devices plotted simultaneously
- Fully asynchronous and GUI-thread safe with `QThread`

## 📦 Requirements

```bash
pip install PyQt5 pyqtgraph bleak
