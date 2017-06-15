import logging

class Logger:
    def __init__(self, local):
        self.logger = logging.getLogger(__name__)
        self.local = local

    def debug(self, msg):
        self.logger.debug("Req %s: %s", self.local.transport._obj_id, msg)
        
    def info(self, msg):
        self.logger.info("Req %s: %s", self.local.transport._obj_id, msg)

    def warning(self, msg):
        self.logger.warning("Req %s: %s", self.local.transport._obj_id, msg)

    def error(self, msg):
        self.logger.error("Req %s: %s", self.local.transport._obj_id, msg)

    def critical(self, msg):
        self.logger.critical("Req %s: %s", self.local.transport._obj_id, msg)

