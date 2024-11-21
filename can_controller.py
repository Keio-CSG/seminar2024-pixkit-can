import can
import time
import threading
from typing import Optional

def read_debug_file(debug_file: str) -> dict[int, list[int]]:
    message_to_send: dict[int, list[int]] = {}
    with open(debug_file, "r") as f:
        for line in f:
            msg_id, msg_data = line.strip().split(":")
            msg_id = int(msg_id, 16)
            msg_data = [int(x, 16) for x in msg_data.split(" ")]
            message_to_send[msg_id] = msg_data
    return message_to_send

def print_send_message(message_to_send: dict[int, list[int]]) -> None:
    # スロットル・ブレーキ・ステアリングの値をprint
    throttle = (message_to_send[0x100][3] * 256 + message_to_send[0x100][4]) / 10.0
    brake = (message_to_send[0x101][3] * 256 + message_to_send[0x101][4]) / 10.0
    steer = (message_to_send[0x102][3] * 256 + message_to_send[0x102][4]) - 500.0

    print(f"OPERATION>>> Throttle: {throttle:.1f} %, Brake: {brake:.1f} %, Steering: {steer:.1f} deg")

class CanController:
    def __init__(self, is_debug: bool = False, debug_file: Optional[str] = None) -> None:
        if not is_debug:
            self.bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=500000)

        self.message_to_send: dict[int, list[int]] = {
            0x100: [0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], # throttle
            0x101: [0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], # brake
            0x102: [0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], # steering
            0x103: [0x01, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], # gear
            0x104: [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], # park
            0x105: [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], # vehicle mode
        }
        self.is_debug = is_debug
        if debug_file is not None:
            self.message_received = read_debug_file(debug_file)
        else:
            self.message_received: dict[int, list[int]] = {}
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
        if not self.is_debug:
            self.bus.shutdown()

    def run_sender(self):
        if self.is_debug:
            while self._sender_flag:
                print_send_message(self.message_to_send)
                time.sleep(0.1)
            return
        while self._sender_flag:
            for msg_id, msg_data in self.message_to_send.items():
                msg = can.Message(arbitration_id=msg_id, data=msg_data, is_extended_id=False)
                self.bus.send(msg)
            time.sleep(0.01)

    def run_receiver(self):
        if self.is_debug:
            return
        while self._receiver_flag:
            for i, msg in enumerate(self.bus):
                self.message_received[msg.arbitration_id] = msg.data
                if i > 20:
                    break
            time.sleep(0.05)
