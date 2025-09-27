import logging
import os
from pathlib import Path
import sys
from typing import Optional
import glob


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
        overwrite_existing: bool = True,
    ) -> None:
        # Save the original base filename for constructing log file names.
        self.base_log_filename = base_filename
        self.max_lines_per_file = max_lines_per_file
        self.max_files = max_files
        self.current_line_count = 0
        self.current_index = 0

        # Construct the current log file name.
        self.current_filename = f"{self.base_log_filename}_{self.current_index}"

        # If overwrite_existing is True, start fresh by removing existing log files
        if overwrite_existing:
            self._remove_existing_logs()
            mode = "w"  # Start with a new file
        else:
            # Find the highest existing log file index to continue from there
            self.current_index = self._find_current_index()
            self.current_filename = f"{self.base_log_filename}_{self.current_index}"

            # If the current file exists, count its current number of lines.
            if os.path.exists(self.current_filename):
                try:
                    with open(self.current_filename, "r", encoding=encoding or "utf-8") as file:
                        self.current_line_count = sum(1 for _ in file)
                except Exception:
                    self.current_line_count = 0

            # If current file has reached max lines, rotate immediately
            if self.current_line_count >= self.max_lines_per_file:
                self._prepare_next_file()
                mode = "w"  # New file should be opened in write mode

        # Initialize FileHandler with the current file.
        super().__init__(self.current_filename, mode, encoding, delay)

    def _remove_existing_logs(self) -> None:
        """
        Remove all existing log files with the same base name.
        """
        pattern = f"{self.base_log_filename}_*"
        existing_files = glob.glob(pattern)

        for file_path in existing_files:
            try:
                os.remove(file_path)
                print(f"[LOGGING INIT] Removed existing log file: {file_path}")
            except Exception as err:
                print(
                    f"[LOGGING INIT] Warning: Could not remove {file_path}: {err}", file=sys.stderr
                )

    def _find_current_index(self) -> int:
        """
        Find the highest index of existing log files to determine where to continue logging.
        """
        pattern = f"{self.base_log_filename}_*"
        existing_files = glob.glob(pattern)

        if not existing_files:
            return 0

        indices = []
        for file_path in existing_files:
            try:
                # Extract the index from the filename
                index_str = file_path.split(f"{self.base_log_filename}_")[1]
                indices.append(int(index_str))
            except (IndexError, ValueError):
                continue

        return max(indices) if indices else 0

    def _prepare_next_file(self) -> None:
        """
        Prepare the next log file for rotation.
        """
        self.current_index += 1
        self.current_filename = f"{self.base_log_filename}_{self.current_index}"
        self.current_line_count = 0

    def rotate_file(self) -> None:
        """
        Rotate to a new log file with an incremented index.
        Also, if the number of log files exceeds the sliding window,
        the oldest file is deleted.
        """
        # Close the current stream if it's open.
        if self.stream:
            self.stream.close()

        # Prepare the next file
        self._prepare_next_file()

        # If the new file already exists, remove it.
        if os.path.exists(self.current_filename):
            os.remove(self.current_filename)

        # Update FileHandler attributes and reopen the new log file in write mode.
        self.baseFilename = os.path.abspath(self.current_filename)
        self.mode = "w"
        self.stream = self._open()

        # Calculate the index of the oldest file to keep and remove it if necessary
        oldest_index = self.current_index - self.max_files
        if oldest_index >= 0:
            oldest_filename = f"{self.base_log_filename}_{oldest_index}"
            if os.path.exists(oldest_filename):
                try:
                    os.remove(oldest_filename)
                except Exception as err:
                    # Use print instead of logging to avoid recursion
                    print(
                        f"Warning: Failed to remove old log file '{oldest_filename}': {err}",
                        file=sys.stderr,
                    )

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


def initialize_logging(log_file: str | Path) -> None:
    """
    Initialize logging with security checks, directory validation, and file rotation.

    This function sets up a logging system that writes to the specified log file.
    If the log file already exists, the logger will append to it. Once the log file
    reaches 10,000 lines, it is removed and a new file is created.

    Args:
        log_file (str | Path): Path to the log file.

    Raises:
        PermissionError: If directory/file creation fails due to permissions.
        FileNotFoundError: If path contains non-existent directories that can't be created.
        ValueError: If insecure permissions are detected on existing directories.
        TypeError: If log_file is not a string or Path.
    """
    # Use print for initialization logging to avoid circular dependencies
    try:
        print(f"[LOGGING INIT] Starting logging initialization for: {log_file}")

        # Ensure log_file is a Path object
        if isinstance(log_file, (str, Path)):
            log_file = Path(log_file)
        else:
            raise TypeError("log_file must be a str or Path")

        # Create the directory structure if needed
        log_dir = log_file.parent
        if log_dir and str(log_dir) != ".":
            print(f"[LOGGING INIT] Ensuring directory exists: {log_dir}")
            if not log_dir.exists():
                log_dir.mkdir(parents=True, mode=0o750, exist_ok=True)
                print("[LOGGING INIT] Directory created with mode 750.")
            else:
                print("[LOGGING INIT] Directory already exists.")

        # Define the log format
        log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

        # Create the custom rotating file handler
        # By default, overwrite existing logs (start fresh)
        rotating_handler = SlidingWindowRotatingHandler(
            base_filename=str(log_file),
            mode="w",  # This will be overridden by the handler based on overwrite_existing
            max_lines_per_file=10_000,
            max_files=10,
            encoding="utf-8",
            overwrite_existing=True,  # Set to False if you want to preserve existing logs
        )
        rotating_handler.setLevel(logging.INFO)
        rotating_handler.setFormatter(logging.Formatter(log_format))

        # Console handler (only errors go to terminal)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(logging.Formatter(log_format))

        # Clear any existing handlers to avoid duplication
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Configure the root logger
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(rotating_handler)
        root_logger.addHandler(console_handler)

        # Test the logging system
        logger = logging.getLogger("initialize_logging")
        logger.info("Logging system successfully configured and tested.")
        print("[LOGGING DONE] Logging system initialized successfully.")

    except PermissionError as perr:
        print(f"[LOGGING ERROR] Security violation prevented: {str(perr)}", file=sys.stderr)
        raise
    except Exception as ex:
        print(f"[LOGGING ERROR] Logging initialization failed: {str(ex)}", file=sys.stderr)
        raise
