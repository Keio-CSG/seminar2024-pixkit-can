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
            time.sleep(0.1)
    except KeyboardInterrupt:
        controller.close()
        print("Exit")


if __name__ == "__main__":
    main()
