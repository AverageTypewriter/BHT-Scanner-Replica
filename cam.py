import cv2
import sys

def initialize_camera():
    # Try different camera indices and backends
    for i in range(0, 3):  # Try indices 0-2
        # Try different backends
        for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
            cap = cv2.VideoCapture(i, backend)
            if cap.isOpened():
                print(f"Camera opened at index {i} with backend {backend}")
                return cap
            cap.release()
    
    print("ERROR: Could not open any camera", file=sys.stderr)
    print("Troubleshooting steps:")
    print("1. Check camera connection")
    print("2. Close other apps using camera")
    print("3. Check camera permissions")
    print("4. Update camera drivers")
    return None

def main():
    cap = initialize_camera()
    if not cap:
        return
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
                
            cv2.imshow("Camera Test", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()