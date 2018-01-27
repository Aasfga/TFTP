import time


class Stopwatch:
    def __init__(self):
        self.data = dict()

    def add_time(self, name, t):
        self.data[name].append(t)

    def get_average(self, name):
        return 1 / len(self.data[name]) * sum(self.data[name])

    def watch(self, name, fun):
        def watched_fun(*args, **kwargs):
            begin = time.time()
            result = fun(*args, **kwargs)
            end = time.time()
            self.add_time(name, end - begin)
            return result
        self.data[name] = []
        return watched_fun
