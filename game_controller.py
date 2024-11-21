import pygame

class GameController:
    def __init__(self, is_debug: bool = False):
        if not is_debug:
            pygame.joystick.init()
            try:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                print("Joystick found:", self.joystick.get_name())
            except pygame.error:
                print("No joystick found")
                raise Exception("No joystick found")

        self.is_debug = is_debug

        pygame.init()

        self.screen = pygame.display.set_mode((600, 400))

    def set_opencv_image(self, opencv_image):
        opencv_image = opencv_image[:,:,::-1]
        shape = opencv_image.shape[1::-1]
        pygame_image = pygame.image.frombuffer(opencv_image.tobytes(), shape, "BGR")
        self.screen.blit(pygame_image, (0, 0))
        pygame.display.flip()

    def update(self):
        if not self.is_debug:
            pygame.event.get()

    def close(self):
        pygame.quit()
        if not self.is_debug:
            self.joystick.quit()
    