import can
import time
import threading
import numpy as np
import cv2

class CanController:
    def __init__(self) -> None:
        self.bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=500000)

        self.message_to_send: dict[int, bytearray] = {}
        self.message_received: dict[int, bytearray] = {}
        self._sender_flag = True
        self._receiver_flag = True

        self.sender_thread = threading.Thread(target=self.run_sender)
        self.sender_thread.start()
        self.receiver_thread = threading.Thread(target=self.run_receiver)
        self.receiver_thread.start()

    def close(self):
        self._sender_flag = False
        self._receiver_flag = False
        self.sender_thread.join()
        self.receiver_thread.join()
        self.bus.shutdown()

    def run_sender(self):
        while self._sender_flag:
            for msg_id, msg_data in self.message_to_send.items():
                msg = can.Message(arbitration_id=msg_id, data=msg_data)
                self.bus.send(msg)
            time.sleep(0.05)

    def run_receiver(self):
        while self._receiver_flag:
            for i, msg in enumerate(self.bus):
                self.message_received[msg.arbitration_id] = msg.data
                if i > 20:
                    break
            time.sleep(0.05)

def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, -angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h))
    return rotated

def display_values(speed, throttle, brake, steer, steering_wheel_img):
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.putText(img, f"Speed: {speed:.2f} m/s", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, f"Throttle: {throttle:.2f} %", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, f"Brake: {brake:.2f} %", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, f"Steering: {steer:.2f} deg", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Draw throttle bar
    throttle_width = int(throttle * 2)  # Scale throttle to fit in the bar
    cv2.rectangle(img, (50, 270), (50 + throttle_width, 290), (0, 255, 0), -1)
    cv2.putText(img, "Throttle", (50, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Draw brake bar
    brake_width = int(brake * 2)  # Scale brake to fit in the bar
    cv2.rectangle(img, (50, 320), (50 + brake_width, 340), (0, 0, 255), -1)
    cv2.putText(img, "Brake", (50, 315), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Resize and draw steering wheel
    steering_wheel_img = cv2.resize(steering_wheel_img, (100, 100))
    rotated_steering_wheel = rotate_image(steering_wheel_img, -steer)
    x_offset = 400
    y_offset = 100
    y1, y2 = y_offset, y_offset + rotated_steering_wheel.shape[0]
    x1, x2 = x_offset, x_offset + rotated_steering_wheel.shape[1]

    alpha_s = rotated_steering_wheel[:, :, 2] / 255.0
    alpha_l = 1.0 - alpha_s

    for c in range(0, 3):
        img[y1:y2, x1:x2, c] = (alpha_s * rotated_steering_wheel[:, :, c] +
                                alpha_l * img[y1:y2, x1:x2, c])

    cv2.imshow("Vehicle Data", img)
    cv2.waitKey(1)

def main():
    controller = CanController()
    steering_wheel_img = cv2.imread("steering.jpg")
    speed = 0.0
    throttle = 0.0
    brake = 0.0
    steer = 0.0

    try:
        while True:
            # 現在速度・アクセル・ブレーキ・ステアリングの値をprint
            received_data = controller.message_received
            if 0x505 in received_data:
                report_vcu = received_data[0x505]
                # speed_raw = (report_vcu[2] << 8) + report_vcu[3]
                # speed_raw_signed = -((speed_raw ^ 0xFFFF) + 1) if report_vcu[2] & 0x80 else speed_raw
                # speed = speed_raw_signed / 1000.0 # m/s
                speed = int.from_bytes(report_vcu[2:4], 'big', signed=True) / 1000.0
                print(f"Speed: {speed} m/s")
            if 0x500 in received_data:
                report_throttle = received_data[0x500]
                # throttle = ((report_throttle[3] << 8) + report_throttle[4]) / 10.0 # %
                throttle = int.from_bytes(report_throttle[3:5], 'big') / 10.0
                print(f"Throttle: {throttle} %")
            if 0x501 in received_data:
                report_brake = received_data[0x501]
                # brake = ((report_brake[3] << 8) + report_brake[4]) / 10.0
                brake = int.from_bytes(report_brake[3:5], 'big') / 10.0
                print(f"Brake: {brake} %")
            if 0x502 in received_data:
                report_steer = received_data[0x502]
                # steer = ((report_steer[3] << 8) + report_steer[4]) - 500
                steer = int.from_bytes(report_steer[3:5], 'big') - 500
                print(f"Steering: {steer} deg")

            # Display vehicle data
            display_values(speed, throttle, brake, steer, steering_wheel_img)
            time.sleep(0.1)
    except KeyboardInterrupt:
        controller.close()
        print("Exit")


if __name__ == "__main__":
    main()
