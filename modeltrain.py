from ultralytics import YOLO

def train_model():
    model = YOLO("yolov8m.pt")
    model.train(
        data="C:/Users/Nikhil Singhvi/OneDrive/Desktop/New folder/CrashDataset/data.yaml",
        epochs=100,
        imgsz=640,
        batch=16,
        device=0,
        workers=4
    )

if __name__ == "__main__":
    train_model()
