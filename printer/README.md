## Calling as a subprocess

Use `uv run --only-group printer --frozen -m printer`.

## Environment Variables

`IPOPS_PRINTER_LOG_LEVEL`: The logging level of the long-lived printer process. (One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.)

`IPOPS_PRINTER_MAX_BUFFER_SIZE`: The maximum amount of data to wait for before printing a single IPoPS frame.

`IPOPS_PRINTER_MIN_CONTIGUOUS_BUFFER_SIZE`: The minimum contiguous amount of data to wait for with minimal timeout before printing all buffered IPoPS frames.

`IPOPS_PRINTER_CONTIGUOUS_DATA_TIMEOUT`: The amount of time to wait before printing the buffered IPoPS frames, even if `IPOPS_PRINTER_MIN_CONTIGUOUS_BUFFER_SIZE` has not been reached.

`IPOPS_PRINTER_NEW_FRAME_POLLING_RATE`: The amount of time to wait before checking for new data after successfully sending a set of print jobs.

`IPOPS_PRINTER_PDF_DATA_FORMAT`: The format of data printed onto each IPoPS fram. (One of `TEXT` or `DATA_MATRIX`.)
