import time
import numpy as np
import cv2
import pygame

from can_controller import CanController

def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, -angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h))
    return rotated

def display_values(speed, throttle, brake, steer, steering_wheel_img, screen):
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
        
    opencv_image = img[:,:,::-1]
    shape = opencv_image.shape[1::-1]
    pygame_image = pygame.image.frombuffer(opencv_image.tobytes(), shape, "BGR")
    screen.blit(pygame_image, (0, 0))
    pygame.display.flip()

    # cv2.imshow("Vehicle Data", img)
    # cv2.waitKey(1)

def main():
    pygame.joystick.init()
    try:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print("Joystick found:", joystick.get_name())
    except pygame.error:
        print("No joystick found")
        return
    
    pygame.init()
    screen = pygame.display.set_mode((600, 400))

    # while True:
    #     for event in pygame.event.get():
    #         if event.type == pygame.JOYAXISMOTION:
    #             print("Axis", event.axis, "motion", event.value)
    #         elif event.type == pygame.JOYBUTTONDOWN:
    #             print("Button", event.button, "down")
    #         elif event.type == pygame.JOYBUTTONUP:
    #             print("Button", event.button, "up")
    #         elif event.type == pygame.JOYHATMOTION:
    #             print("Hat", event.hat, "motion", event.value)
    #         elif event.type == pygame.QUIT:
    #             pygame.quit()
    #             return
    # return

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
                # print(f"Speed: {speed} m/s")
            if 0x500 in received_data:
                report_throttle = received_data[0x500]
                # throttle = ((report_throttle[3] << 8) + report_throttle[4]) / 10.0 # %
                throttle = int.from_bytes(report_throttle[3:5], 'big') / 10.0
                # print(f"Throttle: {throttle} %")
            if 0x501 in received_data:
                report_brake = received_data[0x501]
                # brake = ((report_brake[3] << 8) + report_brake[4]) / 10.0
                brake = int.from_bytes(report_brake[3:5], 'big') / 10.0
                # print(f"Brake: {brake} %")
            if 0x502 in received_data:
                report_steer = received_data[0x502]
                # steer = ((report_steer[3] << 8) + report_steer[4]) - 500
                steer = int.from_bytes(report_steer[3:5], 'big') - 500
                # print(f"Steering: {steer} deg")

            # Display vehicle data
            display_values(speed, throttle, brake, steer, steering_wheel_img, screen)

            # Joystick control
            events = pygame.event.get()
            steer_control = joystick.get_axis(0)
            throttle_brake_control = joystick.get_axis(4)
            steer_value = -int(steer_control * 270)
            throttle_value = int(-min(0, throttle_brake_control) * 100)
            brake_value = int(max(0, throttle_brake_control) * 100)
            print(f"Steer: {steer_value}, Throttle: {throttle_value}, Brake: {brake_value}")

            # Send control data
            # steering
            controller.message_to_send[0x102] = [
                0x01, # enControl
                0x00, # speed
                0x00,
                (steer_value + 500) >> 8,
                (steer_value + 500) & 0xFF,
                0x00,
                0x00,
                0x00,
            ]
            # throttle
            controller.message_to_send[0x100] = [
                0x01, # enControl+
                0x00,
                0x00,
                ((throttle_value * 10) >> 8),
                ((throttle_value * 10) & 0xFF),
                0x00,
                0x00,
                0x00,
            ]
            # brake
            controller.message_to_send[0x101] = [
                0x01, # enControl
                0x00,
                0x00,
                ((brake_value * 10) >> 8),
                ((brake_value * 10) & 0xFF),
                0x00,
                0x00,
                0x00,
            ]
            controller.message_to_send[0x103] = [1,4,0,0,0,0,0,0] # gear
            controller.message_to_send[0x104] = [0,0,0,0,0,0,0,0] # park
            controller.message_to_send[0x105] = [0,0,0,0,0,0,0,0] # vehicle mode

            time.sleep(0.1)
    except KeyboardInterrupt:
        controller.close()
        print("Exit")


if __name__ == "__main__":
    main()
