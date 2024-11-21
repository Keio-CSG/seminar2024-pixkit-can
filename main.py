import time
import numpy as np
import sys
from typing import Optional
import cv2

from can_controller import CanController
from game_controller import GameController

def main(is_debug: bool = False, debug_file: Optional[str] = None, use_joy: bool = False):
    game_controller = GameController(is_debug)
    can_controller = CanController(is_debug, debug_file)
    throttle = 0.0
    brake = 0.0
    steer = 0.0

    try:
        while True:
            ##################################################################
            ########################## 編集範囲 ##############################
            ##################################################################
            # メッセージを可視化
            received_data = can_controller.message_received
            for msg_id, msg_data in received_data.items():
                print(f"ID: {msg_id}, Data: {msg_data}")
            # if 0x500 in received_data:
            #     report_throttle = received_data[0x500]
            #     throttle = ((report_throttle[3] << 8) + report_throttle[4]) / 10.0 # %

            # メッセージをGUIで表示
            img = np.zeros((400, 600, 3), dtype=np.uint8)
            # img = cv2.putText(img, f"Throttle: {0.0} %", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            game_controller.set_opencv_image(img)

            # ジョイスティック入力を受け取る
            op_throttle = 0.0
            op_brake = 0.0
            op_steer = 0.0
            game_controller.update()
            if use_joy:
                joystick = game_controller.joystick

            # 司令値を送信
            # throttle
            # can_controller.message_to_send[0x100] = [
            #     0x01,
            #     0x00,
            #     0x00,
            #     0x00,
            #     0x00,
            #     0x00,
            #     0x00,
            #     0x00,
            # ]
            
            ##################################################################
            ########################## ここまで ##############################
            ##################################################################

            time.sleep(0.1)
    except KeyboardInterrupt:
        game_controller.close()
        can_controller.close()
        print("Exit")


if __name__ == "__main__":
    is_debug = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--debug":
            is_debug = True
    debug_file = None
    if is_debug:
        if "debug_1.txt" in sys.argv:
            debug_file = "debug_1.txt"
        elif "debug_2.txt" in sys.argv:
            debug_file = "debug_2.txt"
    use_joy = False
    if len(sys.argv) > 2:
        if sys.argv[2] == "--joy":
            use_joy = True
    main(is_debug, debug_file, use_joy)
