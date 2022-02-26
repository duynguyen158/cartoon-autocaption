# Deep Learning with PyTorch by Eli Stevens, Luca Antiga, and Thomas Viehmann
# https://github.com/deep-learning-with-pytorch/dlwpt-code/blob/master/util/logconf.py

import logging
import logging.handlers

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Some libraries attempt to add their own root logger handlers. This is
# annoying and so we get rid of them.
for handler in list(root_logger.handlers):
    root_logger.removeHandler(handler)

logfmt_str = "%(asctime)s %(levelname)-8s pid:%(process)d %(name)s:%(lineno)03d:%(funcName)s %(message)s"
formatter = logging.Formatter(logfmt_str)

streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
streamHandler.setLevel(logging.DEBUG)

root_logger.addHandler(streamHandler)
