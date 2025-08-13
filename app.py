from flask import Flask, render_template, Response, request
import cv2
from ultralytics import YOLO
import threading
from datetime import datetime
import requests
import time
import os

app = Flask(__name__)

# --- Config ---
MODEL_PATH = "weights/best.pt"
model = YOLO(MODEL_PATH)
alert_sent = False

# --- Telegram Bot Config ---
BOT_TOKEN = ----
CHAT_ID = ----

# --- Telegram Alert Function ---
def send_telegram_alert(confidence, frame):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = f"temp_{timestamp}.jpg"
        cv2.imwrite(temp_path, frame)

        with open(temp_path, 'rb') as photo:
            message = f"🚨 Crash Detected with {confidence:.2f} confidence!"
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            payload = {
                "chat_id": CHAT_ID,
                "caption": message
            }
            files = {"photo": photo}
            response = requests.post(url, data=payload, files=files)
            if response.status_code == 200:
                print("[✅] Telegram alert sent")
            else:
                print(f"[❌] Error: {response.status_code}, {response.text}")

        os.remove(temp_path)

    except Exception as e:
        print(f"[❌] Telegram error: {e}")

# --- Reset Alert Flag ---
def reset_alert_flag(delay=10):
    global alert_sent
    time.sleep(delay)
    alert_sent = False

# --- Detection and Streaming ---
def generate_frames(conf_threshold):
    global alert_sent
    cap = cv2.VideoCapture(0)

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            results = model(frame, verbose=False)

            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    xyxy = box.xyxy[0].cpu().numpy().astype(int)

                    if conf > conf_threshold:
                        label = f"{model.names[cls]} {conf:.2f}"
                        cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0, 0, 255), 2)
                        cv2.putText(frame, label, (xyxy[0], xyxy[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                        if not alert_sent:
                            threading.Thread(target=send_telegram_alert, args=(conf, frame.copy())).start()
                            threading.Thread(target=reset_alert_flag).start()
                            alert_sent = True

            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    conf = float(request.args.get("conf", 0.6))
    return Response(generate_frames(conf),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)

