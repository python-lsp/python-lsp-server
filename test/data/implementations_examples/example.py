from abc import ABC, abstractmethod


class Animal(ABC):
    @abstractmethod
    def breathe(self):
        pass

    @property
    @abstractmethod
    def size(self) -> str:
        pass

class WingedAnimal(Animal):
    @abstractmethod
    def fly(self, destination):
        pass

class Bird(WingedAnimal):
    def breathe(self):
        print("*inhales like a bird*")

    def fly(self, destination):
        print("*flies like a bird*")

    @property
    def size(self) -> str:
        return "bird-sized"

print("not a method at all")
