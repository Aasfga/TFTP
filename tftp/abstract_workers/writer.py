import hashlib

import os


class FileWriter:
    def __init__(self):
        self.file = None

    @staticmethod
    def can_create(filename):
        return not os.path.isfile(filename)

    def open(self, filename):
        self.file = open(filename, "wb")

    def save(self, data):
        self.file.write(data)

    def close(self):
        self.file.close()

    @staticmethod
    def delete(filename):
        os.remove(filename)


class PrintWriter:
    def __init__(self):
        self.data = ""

    def can_create(self, filename):
        return True

    def open(self, filename):
        pass

    def save(self, new_data):
        self.data += new_data

    def close(self):
        print(self.data)

    def delete(self, filename):
        pass


class MD5Writer:
    def __init__(self):
        self.hash = hashlib.md5()

    def can_create(self, filename):
        return True

    def open(self, filename):
        pass

    def save(self, new_data):
        self.hash.update(new_data)

    def close(self):
        print(self.hash.hexdigest())

    def delete(self, filename):
        pass
