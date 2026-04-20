#  Disk Scheduling Simulator Pro

A **feature-rich desktop application** built using **Python (Tkinter + Matplotlib)** to simulate and visualize disk scheduling algorithms used in Operating Systems.

---

##  Features

###  Supported Algorithms

* FCFS (First Come First Serve)
* SSTF (Shortest Seek Time First)
* SCAN (Elevator Algorithm)
* C-SCAN (Circular SCAN)
* LOOK
* C-LOOK

---

###  Visualization

* Real-time **animation of disk head movement**
* Step-by-step seek visualization
* Cylinder movement tracking
* Heatmap of disk access frequency

---

###  Performance Analysis

* Total Seek Time calculation
* Average Seek Time per request
* Compare all algorithms simultaneously
* Identify best-performing algorithm

---

###  Data Management

* Run history tracking
* Export results to CSV
* Export complete history

---

###  User Interface

* Modern dark-themed GUI using Tkinter
* Interactive controls
* Algorithm guide section
* One-click simulation from guide

---

##  Tech Stack

* **Language:** Python
* **GUI:** Tkinter
* **Visualization:** Matplotlib
* **Data Handling:** NumPy, CSV
* **Concepts:** Operating Systems (Disk Scheduling)

---

##  Installation

### 1. Install Python (3.8+)

Check version:

```bash id="bq1f3a"
python --version
```

---

### 2. Install Required Libraries

```bash id="e0f4xv"
pip install matplotlib numpy
```

---

##  How to Run

```bash id="p9s7re"
python disk_scheduler_pro_final.py
```

---

##  Input Format

* **Request Queue:** Space-separated values (0–199)

  ```
  98 183 37 122 14 124 65 67
  ```

* **Initial Head Position:**

  ```
  53
  ```

---

##  Algorithms Overview

### 🔹 FCFS

* Processes requests in order of arrival
* Simple but inefficient

### 🔹 SSTF

* Chooses nearest request
* Faster but may cause starvation

### 🔹 SCAN

* Moves like an elevator
* Balanced and fair

### 🔹 C-SCAN

* Moves in one direction only
* Uniform waiting time

### 🔹 LOOK

* Stops at last request instead of disk edge
* More efficient than SCAN

### 🔹 C-LOOK

* Optimized version of C-SCAN
* Best overall performance

---

##  Project Structure

```id="4y6tbc"
disk-scheduler/
│── disk_scheduler_pro_final.py
│── README.md
```

---

##  Concepts Used

* Disk Scheduling Algorithms
* Seek Time Calculation
* Data Visualization
* GUI Development
* Event-driven Programming

---

##  Use Cases

* OS Lab Projects
* Viva Preparation
* Algorithm Comparison
* Educational Demonstrations

---

##  Limitations

* Fixed disk size (0–199 cylinders)
* No real disk hardware interaction
* GUI-based (not web-based)

---

##  Future Enhancements

* Add real-time graph comparison
* Support dynamic disk sizes
* Add more algorithms (e.g., N-Step SCAN)
* Web-based version

---

##  Author

**Your Name**

---

##  License

This project is for educational purposes only.
