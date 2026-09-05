import serial
import sys
import csv
import os
from datetime import datetime

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
BAUD = 115200

custom_out = sys.argv[2] if len(sys.argv) > 2 else None

def make_out_path(save_slot: int, custom_out: str | None) -> str:
  now = datetime.now()
  day_folder = now.strftime("%Y-%m-%d")           # e.g. 2026-08-28
  ts = now.strftime("%H_%M_%S")              # e.g. 20260828_151530

  # Create folder for today's files
  os.makedirs(day_folder, exist_ok=True)
  if custom_out is not None:
    return custom_out
  return os.path.join(day_folder, f"rocket_data_slot_{save_slot}_{ts}.csv")

def safe_int(value: str, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def transform_data(data: list[list[str]]) -> list[list[str]]:
  for row_i, row in enumerate(data):
    if row_i == 0:
      row[0] = "dt_s"
    else:
      row[0] = str(float(row[0]) / 1000.0)
  return data

def save_to_csv(out_path: str, data: list[list[str]]):
  with open(out_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(data)

HEADER = "BEGIN_ROCKET_DATA_"
FOOTER = "END_ROCKET_DATA_"

if __name__ == "__main__":
  with serial.Serial(PORT, BAUD, timeout = 2) as ser:
    in_frame = False
    cur_data_slot = 0
    data: list[list[str]] = []

    while True:
      line = ser.readline().decode("utf-8", errors="replace").strip()

      if not line:
        continue
    
      print(f"SERIAL > {line}")

      if line.startswith(HEADER):
        data_slot = safe_int(line.removeprefix(HEADER))
        if data_slot is None:
          print("Failed to get save slot of header")
          continue
        cur_data_slot = data_slot
        in_frame = True
        cur_line = 0
        data = []
        continue

      if line.startswith(FOOTER):
        data_slot = safe_int(line.removeprefix(FOOTER))
        if data_slot is None:
          print("Failed to get save slot of footer")
          continue
        if not cur_data_slot == data_slot:
          print("Footer has wrong data slot")
          continue
        in_frame = False

        out_path = make_out_path(cur_data_slot, custom_out)
        save_to_csv(out_path, transform_data(data))
        continue

      if not in_frame:
        continue

      parts = line.split(",")
      if not len(parts) == 7:
        print("Invalid line of data")
        continue

      data.append(parts)
