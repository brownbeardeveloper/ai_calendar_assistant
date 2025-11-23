import datetime

class Logger:
    def info(self, message: str):
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} INFO: {message}")

    def error(self, message: str):
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR: {message}")
