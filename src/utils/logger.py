import datetime

class Logger:
    def __init__(self, path: str = "app.log"):
        self.path = path

    def info(self, message: str):
        with open(self.path, "a") as f:
            f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO: {message}\n")

    def error(self, message: str):
        with open(self.path, "a") as f:
            f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR: {message}\n")