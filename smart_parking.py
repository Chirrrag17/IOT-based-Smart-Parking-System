
import threading
import time

import cv2
from ultralytics import YOLO
from flask import Flask, jsonify, render_template_string, Response

# ----------------------------
# Toy car dimensions (approx.)
# ----------------------------
TOY_CAR_LENGTH_CM = 12.0
TOY_CAR_WIDTH_CM = 6.0
TOY_CAR_HEIGHT_CM = 4.0

# ----------------------------
# YOLO model
# ----------------------------
MODEL_PATH = "yolov8n.pt"

# ----------------------------
# Camera calibration
# ----------------------------
CALIBRATION_DISTANCE_CM = 20.0
CALIBRATION_PIXEL_WIDTH = 110.0

FOCAL_LENGTH = (
    CALIBRATION_PIXEL_WIDTH * CALIBRATION_DISTANCE_CM
) / TOY_CAR_WIDTH_CM

# ----------------------------
# Parking slot region
# ----------------------------
PARKING_X1, PARKING_Y1 = 200, 120
PARKING_X2, PARKING_Y2 = 440, 360

# ----------------------------
# Distance threshold
# ----------------------------
DISTANCE_THRESHOLD_CM = 10.0

# ----------------------------
# Shared parking status
# ----------------------------
parking_status = {
    "slot": "VACANT",
    "distance_cm": None,
}

status_lock = threading.Lock()

# Latest webcam frame
latest_frame = None
frame_lock = threading.Lock()

# ----------------------------
# Helper functions
# ----------------------------

def estimate_distance_cm(pixel_width: float) -> float:
    """Estimate distance using a simple pinhole camera model."""

    if pixel_width <= 0:
        return 9999.0

    return (TOY_CAR_WIDTH_CM * FOCAL_LENGTH) / pixel_width


def box_center(x1, y1, x2, y2):
    """Calculate the center of a bounding box."""

    cx = int((x1 + x2) / 2)
    cy = int((y1 + y2) / 2)

    return cx, cy


def is_inside_parking(cx, cy):
    """Check whether the detected object's center is inside the parking slot."""

    return (
        PARKING_X1 <= cx <= PARKING_X2
        and PARKING_Y1 <= cy <= PARKING_Y2
    )


# ----------------------------
# YOLO detection loop
# ----------------------------

def detection_loop(show_window=False):
    global parking_status, latest_frame

    print("[YOLO] Loading model...")

    model = YOLO(MODEL_PATH)

    # External webcam
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print(
            "[ERROR] Could not open webcam at index 1. "
            "Try index 0 or 2."
        )
        cap.release()
        return

    print("[YOLO] Detection loop started.")

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("[ERROR] Failed to capture webcam frame.")
                break

            # Save the latest frame for the website
            with frame_lock:
                latest_frame = frame.copy()

            # COCO class 2 represents a car
            results = model(frame, classes=[2], verbose=False)

            slot_status = "VACANT"
            min_distance_cm = None

            for result in results:
                boxes = result.boxes

                if boxes is None:
                    continue

                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    x1_i = int(x1)
                    y1_i = int(y1)
                    x2_i = int(x2)
                    y2_i = int(y2)

                    cx, cy = box_center(
                        x1_i, y1_i, x2_i, y2_i
                    )

                    pixel_width = x2 - x1

                    distance_cm = estimate_distance_cm(
                        pixel_width
                    )

                    if (
                        min_distance_cm is None
                        or distance_cm < min_distance_cm
                    ):
                        min_distance_cm = distance_cm

                    # A car must be inside the slot region
                    # and within the configured distance.
                    if (
                        is_inside_parking(cx, cy)
                        and distance_cm <= DISTANCE_THRESHOLD_CM
                    ):
                        slot_status = "OCCUPIED"

            # Update the website's shared status
            with status_lock:
                parking_status["slot"] = slot_status

                parking_status["distance_cm"] = (
                    round(min_distance_cm, 1)
                    if min_distance_cm is not None
                    else None
                )

            # Optional debugging window
            if show_window:
                color = (
                    (0, 0, 255)
                    if slot_status == "OCCUPIED"
                    else (0, 255, 0)
                )

                cv2.rectangle(
                    frame,
                    (PARKING_X1, PARKING_Y1),
                    (PARKING_X2, PARKING_Y2),
                    (255, 255, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    f"Slot: {slot_status}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    color,
                    3,
                )

                cv2.imshow("Smart Parking Debug", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            time.sleep(0.05)

    except Exception as error:
        print(f"[ERROR] Detection failed: {error}")

    finally:
        cap.release()
        cv2.destroyAllWindows()

        with status_lock:
            parking_status["slot"] = "VACANT"
            parking_status["distance_cm"] = None

        print("[YOLO] Detection loop stopped.")


# ----------------------------
# Live webcam stream
# ----------------------------

def gen_frames():
    """Generate JPEG frames for the Flask video stream."""

    global latest_frame

    while True:
        with frame_lock:
            frame = (
                None
                if latest_frame is None
                else latest_frame.copy()
            )

        if frame is None:
            time.sleep(0.05)
            continue

        success, buffer = cv2.imencode(".jpg", frame)

        if not success:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )


# ----------------------------
# Flask web application
# ----------------------------

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Smart Parking System</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #0f172a, #020617);
            color: #e5e7eb;
            text-align: center;
            margin: 0;
            padding: 30px 16px;
        }

        h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #93c5fd;
            font-size: 19px;
            margin-bottom: 8px;
        }

        .guide {
            color: #cbd5e1;
            margin-bottom: 30px;
        }

        .layout {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: flex-start;
            gap: 24px;
        }

        .card {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 25px;
            width: 300px;
            box-sizing: border-box;
        }

        .card h2 {
            font-size: 18px;
            color: #cbd5e1;
        }

        .status {
            font-size: 30px;
            font-weight: bold;
            margin: 20px 0;
        }

        .vacant {
            color: #22c55e;
        }

        .occupied {
            color: #ef4444;
        }

        .distance {
            color: #93c5fd;
            font-size: 17px;
        }

        .video-card {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 20px;
            max-width: 660px;
            width: 100%;
            box-sizing: border-box;
        }

        .video-container {
            overflow: hidden;
            border-radius: 12px;
            border: 1px solid #475569;
        }

        .video-container img {
            display: block;
            width: 100%;
            height: auto;
        }

        footer {
            margin-top: 30px;
            font-size: 13px;
            color: #94a3b8;
        }
    </style>
</head>

<body>

    <h1>Dayananda Sagar Academy of Technology and Management</h1>

    <div class="subtitle">
        Mini Project: Smart Parking System
    </div>

    <div class="guide">
        Guide: RV Manjunath Sir
    </div>

    <div class="layout">

        <div class="card">
            <h2>Parking Slot 1</h2>

            <div id="slot-status" class="status vacant">
                VACANT
            </div>

            <div id="distance" class="distance">
                Distance: -- cm
            </div>
        </div>

        <div class="video-card">
            <h2>Live Webcam Feed</h2>

            <div class="video-container">
                <img
                    src="/video_feed"
                    alt="Live webcam feed"
                >
            </div>
        </div>

    </div>

    <footer>
        Smart Parking Demo | YOLOv8 + OpenCV + Flask
    </footer>

    <script>
        async function fetchStatus() {
            try {
                const response = await fetch("/status");
                const data = await response.json();

                const statusElement =
                    document.getElementById("slot-status");

                const distanceElement =
                    document.getElementById("distance");

                const slot = data.slot || "VACANT";
                const distance = data.distance_cm;

                statusElement.textContent = slot;

                statusElement.classList.remove(
                    "vacant",
                    "occupied"
                );

                statusElement.classList.add(
                    slot === "OCCUPIED"
                        ? "occupied"
                        : "vacant"
                );

                distanceElement.textContent =
                    distance === null
                        ? "Distance: -- cm"
                        : "Distance: " + distance + " cm";

            } catch (error) {
                console.error(
                    "Unable to fetch parking status:",
                    error
                );
            }
        }

        fetchStatus();
        setInterval(fetchStatus, 1000);
    </script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@app.route("/status")
def status():
    with status_lock:
        return jsonify(parking_status.copy())


@app.route("/video_feed")
def video_feed():
    return Response(
        gen_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ----------------------------
# Main entry point
# ----------------------------

if __name__ == "__main__":

    # Start YOLO detection in a background thread
    detection_thread = threading.Thread(
        target=detection_loop,
        kwargs={"show_window": False},
        daemon=True,
    )

    detection_thread.start()

    print("[WEB] Starting Flask server...")
    print("[WEB] Open http://127.0.0.1:5000 in your browser.")

    try:
        app.run(
            host="127.0.0.1",
            port=5000,
            debug=False,
            threaded=True,
        )

    except KeyboardInterrupt:
        print("[WEB] Server stopped.")

