import can
import time
import threading

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

def main():
    controller = CanController()

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

            time.sleep(0.1)
    except KeyboardInterrupt:
        controller.close()
        print("Exit")


if __name__ == "__main__":
    main()
