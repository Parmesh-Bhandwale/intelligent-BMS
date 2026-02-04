import logging
import queue
from logging.handlers import QueueHandler, QueueListener
from contextvars import ContextVar

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
LOG_QUEUE = queue.Queue(-1)

# class RequestIdFilter(logging.Filter):
#     def filter(self, record):
#         import contextvars
#         try:
#             record.request_id = request_id_ctx.get()
#         except LookupError:
#             record.request_id = "N/A"
#         return True

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "N/A"
        return True

def setup_logging():
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        # "request_id=%(request_id)s | "
        "%(name)s | %(message)s"
    )


    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    queue_handler = QueueHandler(LOG_QUEUE)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(queue_handler)
    root.addFilter(RequestIdFilter())

    listener = QueueListener(LOG_QUEUE, console_handler)
    listener.start()
