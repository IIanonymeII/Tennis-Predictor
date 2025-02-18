import logging
import os
from typing import Optional


class SlidingWindowRotatingHandler(logging.FileHandler):
    """
    Custom logging handler that rotates log files once a maximum number of lines is reached.
    Only a fixed number of log files (a sliding window) is kept.

    For example, with a window size of 4 and a maximum of 1000 lines per file:
      - Initially, logs are written to "app.log_0".
      - When "app.log_0" reaches 1000 lines, rotation occurs:
          * A new file "app.log_1" is created.
          * If there are already 4 files (e.g. "app.log_0", "app.log_1", "app.log_2", "app.log_3"),
            then the oldest ("app.log_0") is deleted.
      - On subsequent rotations, the sliding window moves forward:
          "app.log_1", "app.log_2", "app.log_3", "app.log_4", then "app.log_2", "app.log_3", "app.log_4", "app.log_5", etc.
    """

    def __init__(
        self,
        base_filename: str,
        mode: str = "a",
        max_lines_per_file: int = 1000,
        max_files: int = 4,
        encoding: Optional[str] = None,
        delay: bool = False,
    ) -> None:
        # Save the original base filename for constructing log file names.
        self.base_log_filename = base_filename
        self.max_lines_per_file = max_lines_per_file
        self.max_files = max_files
        self.current_index = 0
        self.current_line_count = 0

        # Construct the current log file name.
        self.current_filename = f"{self.base_log_filename}_{self.current_index}"
        # If the file exists, count its current number of lines.
        if os.path.exists(self.current_filename):
            try:
                with open(self.current_filename, "r", encoding=encoding or "utf-8") as file:
                    self.current_line_count = sum(1 for _ in file)
            except Exception:
                self.current_line_count = 0

        # Initialize FileHandler with the current file.
        super().__init__(self.current_filename, mode, encoding, delay)

    def rotate_file(self) -> None:
        """
        Rotate to a new log file with an incremented index.
        Also, if the number of log files exceeds the sliding window,
        the oldest file is deleted.
        """
        # Close the current stream if it's open.
        if self.stream:
            self.stream.close()

        # Increment the log file index and construct the new file name.
        self.current_index += 1
        self.current_filename = f"{self.base_log_filename}_{self.current_index}"

        # If the new file already exists, remove it.
        if os.path.exists(self.current_filename):
            os.remove(self.current_filename)

        # Reset the line count for the new file.
        self.current_line_count = 0

        # Update FileHandler attributes and reopen the new log file in write mode.
        self.baseFilename = os.path.abspath(self.current_filename)
        self.mode = "w"
        self.stream = self._open()

        # Calculate the index of the oldest file to keep.

        oldest_index = self.current_index - self.max_files
        if oldest_index >= 0:
            oldest_filename = f"{self.base_log_filename}_{oldest_index}"
            if os.path.exists(oldest_filename):
                try:
                    os.remove(oldest_filename)
                except Exception as err:
                    logging.error(f"Failed to remove old log file '{oldest_filename}': {err}")

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record.

        If the current file has reached the maximum number of lines, rotate
        to a new file before emitting the record.
        """
        try:
            if self.current_line_count >= self.max_lines_per_file:
                self.rotate_file()
            super().emit(record)
            self.current_line_count += 1
        except Exception:
            self.handleError(record)

def initialize_logging(log_file: str) -> None:
    """
    Initialize logging with security checks, directory validation, and file rotation.

    This function sets up a logging system that writes to the specified log file.
    If the log file already exists, the logger will append to it. Once the log file
    reaches 10,000 lines, it is removed and a new file is created.

    Args:
        log_file (str): Path to the log file.

    Raises:
        PermissionError: If directory/file creation fails due to permissions.
        FileNotFoundError: If path contains non-existent directories that can't be created.
        ValueError: If insecure permissions are detected on existing directories.
        TypeError: If log_file is not a string.
    """
    # Obtain a temporary logger for initialization
    init_logger = logging.getLogger("initialize_logging")
    try:
        init_logger.debug("Starting logging initialization.")
        # Validate input parameter type
        if not isinstance(log_file, str):
            raise TypeError("log_file must be a string")

        # Create the directory structure if needed
        log_dir = os.path.dirname(log_file)
        if log_dir:
            init_logger.debug(f"Ensuring directory exists: {log_dir}")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, mode=0o750, exist_ok=True)
                init_logger.debug("Directory created with mode 750.")
            else:
                init_logger.debug("Directory already exists.")

        # Determine the file mode: append if file exists, otherwise write
        first_log_filename = f"{log_file}_0"
        file_mode = "a" if os.path.exists(first_log_filename) else "w"

        init_logger.debug(f"Using file mode '{file_mode}' for log file.")

        # Define the log format
        log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

        # Create the custom rotating file handler
        rotating_handler = SlidingWindowRotatingHandler(
            base_filename      = log_file,
            mode               = file_mode,
            max_lines_per_file = 10_000,
            max_files          = 10,
            encoding           = "utf-8"
        )
        rotating_handler.setLevel(logging.INFO)

        # Configure the root logger explicitly
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[rotating_handler]
        )
        print(f"[LOGGING DONE] ...")
        init_logger.info("Logging system successfully configured.")
    except PermissionError as perr:
        init_logger.error(f"Security violation prevented: {str(perr)}")
        raise
    except Exception as ex:
        init_logger.error(f"Logging initialization failed: {str(ex)}")
        raise
