import sys
import psutil
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QSpinBox, QPushButton, QTabWidget
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class MonitoringTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux Monitoring Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        self.cpu_data = []
        self.mem_data = []
        self.net_sent_data = []
        self.net_recv_data = []
        self.refresh_rate = 2000  # default to 2 seconds
        
        self.initUI()
        self.updateMetrics()

    def initUI(self):
        # Central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Metrics Tab
        self.metrics_tab = QWidget()
        self.metrics_tab_layout = QVBoxLayout()
        self.metrics_tab.setLayout(self.metrics_tab_layout)
        self.tabs.addTab(self.metrics_tab, "Metrics")

        # Graphs Tab
        self.graphs_tab = QWidget()
        self.graphs_tab_layout = QVBoxLayout()
        self.graphs_tab.setLayout(self.graphs_tab_layout)
        self.tabs.addTab(self.graphs_tab, "Graphs")

        # Metrics Widgets
        self.cpu_label = QLabel("CPU Usage: ", self)
        self.mem_label = QLabel("Memory Usage: ", self)
        self.disk_label = QLabel("Disk Usage: ", self)
        self.net_label = QLabel("Network Usage: ", self)
        self.process_table = QTableWidget()
        
        self.process_table.setColumnCount(3)
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "Memory Usage"])
        
        self.refresh_spinner = QSpinBox(self)
        self.refresh_spinner.setRange(1, 60)
        self.refresh_spinner.setValue(2)  # default to 2 seconds
        self.refresh_spinner.valueChanged.connect(self.setRefreshRate)

        self.refresh_button = QPushButton("Set Refresh Rate", self)
        self.refresh_button.clicked.connect(self.updateMetrics)

        self.metrics_tab_layout.addWidget(self.cpu_label)
        self.metrics_tab_layout.addWidget(self.mem_label)
        self.metrics_tab_layout.addWidget(self.disk_label)
        self.metrics_tab_layout.addWidget(self.net_label)
        self.metrics_tab_layout.addWidget(self.process_table)
        self.metrics_tab_layout.addWidget(self.refresh_spinner)
        self.metrics_tab_layout.addWidget(self.refresh_button)

        # Graphs Widgets
        self.cpu_canvas = FigureCanvas(plt.Figure())
        self.mem_canvas = FigureCanvas(plt.Figure())
        self.net_canvas = FigureCanvas(plt.Figure())

        self.graphs_tab_layout.addWidget(self.cpu_canvas)
        self.graphs_tab_layout.addWidget(self.mem_canvas)
        self.graphs_tab_layout.addWidget(self.net_canvas)

        # Timer to update metrics
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateMetrics)
        self.timer.start(self.refresh_rate)

    def setRefreshRate(self):
        self.refresh_rate = self.refresh_spinner.value() * 1000  # Convert seconds to milliseconds
        self.timer.setInterval(self.refresh_rate)

    def updateMetrics(self):
        # Update CPU, Memory, Disk, and Network Usage
        cpu_usage = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        
        self.cpu_label.setText(f"CPU Usage: {cpu_usage}%")
        self.mem_label.setText(f"Memory Usage: {mem.percent}%")
        self.disk_label.setText(f"Disk Usage: {disk.percent}%")
        self.net_label.setText(f"Network Usage - Sent: {net.bytes_sent / (1024 ** 2):.2f} MB, Received: {net.bytes_recv / (1024 ** 2):.2f} MB")

        # Update Process Information
        self.updateProcesses()
        
        # Collect data for plots
        self.cpu_data.append(cpu_usage)
        self.mem_data.append(mem.percent)
        self.net_sent_data.append(net.bytes_sent / (1024 ** 2))  # in MB
        self.net_recv_data.append(net.bytes_recv / (1024 ** 2))  # in MB

        # Limit data size to 100 points for plotting
        max_data_points = 100
        if len(self.cpu_data) > max_data_points:
            self.cpu_data = self.cpu_data[-max_data_points:]
            self.mem_data = self.mem_data[-max_data_points:]
            self.net_sent_data = self.net_sent_data[-max_data_points:]
            self.net_recv_data = self.net_recv_data[-max_data_points:]

        self.plotMetrics()

    def updateProcesses(self):
        processes = [(p.pid, p.name(), p.memory_info().rss / (1024 ** 2)) for p in psutil.process_iter(['pid', 'name', 'memory_info'])]

        self.process_table.setRowCount(len(processes))
        
        for i, (pid, name, mem) in enumerate(processes):
            self.process_table.setItem(i, 0, QTableWidgetItem(str(pid)))
            self.process_table.setItem(i, 1, QTableWidgetItem(name))
            self.process_table.setItem(i, 2, QTableWidgetItem(f"{mem:.2f} MB"))

    def plotMetrics(self):
        # Plot CPU Usage
        self.plot(self.cpu_canvas, "CPU Usage", self.cpu_data, "CPU Usage (%)", "CPU Usage Over Time")

        # Plot Memory Usage
        self.plot(self.mem_canvas, "Memory Usage", self.mem_data, "Memory Usage (%)", "Memory Usage Over Time")

        # Plot Network Usage
        self.plotNetworkUsage()

    def plot(self, canvas, title, data, ylabel, xlabel):
        canvas.figure.clear()
        ax = canvas.figure.add_subplot(111)
        ax.plot(data, label=title)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel(xlabel)
        ax.legend()
        canvas.draw()

    def plotNetworkUsage(self):
        self.net_canvas.figure.clear()
        ax = self.net_canvas.figure.add_subplot(111)
        ax.plot(self.net_sent_data, label="Sent", color='blue')
        ax.plot(self.net_recv_data, label="Received", color='green')
        ax.set_title("Network Usage Over Time")
        ax.set_ylabel("Network Usage (MB)")
        ax.set_xlabel("Time")
        ax.legend()
        self.net_canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MonitoringTool()
    window.show()
    sys.exit(app.exec_())

