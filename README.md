# IoT-Based Smart Parking System

## Overview

This project demonstrates a smart parking system combining computer vision, IoT hardware components, and a web-based monitoring interface.

The system includes a Python-based vehicle detection application and an Arduino-based gate control system.

## Features

### Computer Vision and Web Dashboard

* Vehicle detection using YOLOv8.
* Image processing using OpenCV.
* Parking-slot status monitoring.
* Approximate distance estimation using camera calibration.
* Live webcam streaming through Flask.
* Web dashboard displaying parking status and estimated distance.

### Arduino-Based Gate Control

* IR sensor for object detection.
* HC-SR04 ultrasonic sensor for distance measurement.
* Servo motor for automatic gate operation.
* LED indicator.
* Serial output for monitoring sensor readings and gate status.

## Technologies Used

* Python
* Arduino C++
* YOLOv8
* OpenCV
* Flask
* HTML, CSS, and JavaScript

## Hardware Components

* Arduino-compatible microcontroller
* IR sensor
* HC-SR04 ultrasonic sensor
* Servo motor
* LED
* USB webcam
* Toy car for demonstration
* Connecting wires and suitable power supply

## Software Requirements

* Python
* Arduino IDE
* Visual Studio Code
* Required Python packages listed in `requirements.txt`

## Project Structure

```text
iot-smart-parking-system/
├── smart_parking.py
├── requirements.txt
├── README.md
└── arduino/
    └── smart_parking.ino
```

## Running the Python Application

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Start the application:

```bash
python smart_parking.py
```

Open the dashboard at:

`http://127.0.0.1:5000`

Ensure that the webcam index in the Python code matches the connected camera.

## Uploading the Arduino Program

1. Open `arduino/smart_parking.ino` in Arduino IDE.
2. Connect the Arduino board to your computer.
3. Select the correct board and COM port.
4. Upload the program.
5. Open Serial Monitor at 115200 baud to view sensor readings and gate status.

## Current Implementation

The Python application performs webcam-based vehicle detection and displays parking information through a Flask dashboard.

The Arduino program independently reads the IR and ultrasonic sensors and controls the servo gate.

**Note:** The Python and Arduino programs currently operate independently. Communication between them and unified parking-status synchronization can be added as a future enhancement.

## Future Improvements

* Integrate Python and Arduino through serial communication.
* Synchronize parking status with the hardware.
* Support multiple parking slots.
* Store parking information in a database.
* Add remote monitoring capabilities.
