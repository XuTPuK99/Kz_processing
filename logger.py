import logging

file_log = logging.FileHandler("trying_log.log", encoding="utf8", mode="w")
formatter_f = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
file_log.setFormatter(formatter_f)
file_log.setLevel(logging.WARNING)

console_out = logging.StreamHandler()
formatter_s = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
console_out.setFormatter(formatter_s)
console_out.setLevel(logging.INFO)


logger = logging.getLogger("logger")
logger.addHandler(file_log)
logger.addHandler(console_out)
logger.setLevel(logging.INFO)
