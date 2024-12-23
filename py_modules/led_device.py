from abc import ABC, abstractmethod

from py_modules.utils import Color


class LEDDevice(ABC):
    @abstractmethod
    def set_color(self, color: Color, brightness: int):
        pass

    @abstractmethod
    def set_mode(self, mode: str):
        pass
