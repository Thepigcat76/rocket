import serial
import sys
import csv
import os
from datetime import datetime

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
BAUD = 115200

now = datetime.now()
day_folder = now.strftime("%Y-%m-%d")           # e.g. 2026-08-28
ts = now.strftime("%H_%M_%S")              # e.g. 20260828_151530

# Create folder for today's files
os.makedirs(day_folder, exist_ok=True)

default_out = os.path.join(day_folder, f"rocket_data_{ts}.csv")
OUT = sys.argv[2] if len(sys.argv) > 2 else default_out
try:
    with serial.Serial(PORT, BAUD, timeout=2) as ser, open(OUT, "w", newline="") as f:
        writer = csv.writer(f)
        in_frame = False
        header_written = False

        print(f"Listening on {PORT}...")
        print(f"Saving to {OUT}")

        while True:
            line = ser.readline().decode("utf-8", errors="replace").strip()

            if line:
                print(f"SERIAL > {line}")

            if not line:
                continue

            if line == "BEGIN_ROCKET_DATA":
                in_frame = True
                header_written = False
                print("Transfer started")
                continue

            if line == "END_ROCKET_DATA":
                print("Transfer complete")
                break

            if not in_frame:
                continue

            if not header_written:
                parts = line.split(",")
                parts[0] = "dt_s"
                writer.writerow(parts)
                header_written = True
                continue

            parts = line.split(",")
            parts[0] = f"{float(parts[0]) / 1000.0}"
            if len(parts) == 7:
                writer.writerow(parts)
except:
    if os.path.getsize(OUT) == 0:
        os.remove(OUT)
        print(f"Removed file")
    else:
        print(f"Saved to {OUT}")
