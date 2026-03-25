#!/usr/bin/env python3
"""FTX-1 CDC USB endpoint probe — requires sudo."""

import struct
import time

import usb.core
import usb.util


def main():
    dev = usb.core.find(idVendor=0x26AA, idProduct=0x0030)
    if not dev:
        print("CDC device (26AA:0030) not found")
        return

    print(f"Found: {dev.manufacturer} {dev.product}")

    # Detach kernel driver so we get raw access
    for intf in [0, 1]:
        if dev.is_kernel_driver_active(intf):
            dev.detach_kernel_driver(intf)
            print(f"Detached kernel driver from IF{intf}")

    dev.set_configuration()
    print("Config set.\n")

    # 1. Interrupt EP 0x83 — serial state notifications
    print("=== 1. Interrupt EP 0x83 (serial state) ===")
    got_intr = False
    for i in range(10):
        try:
            data = dev.read(0x83, 16, timeout=500)
            print(f"  INTR [{i}]: {bytes(data).hex()}")
            got_intr = True
        except usb.core.USBTimeoutError:
            pass
    if not got_intr:
        print("  No interrupt data (10 × 500ms)")

    # 2. Bulk IN 0x81 — passive read
    print("\n=== 2. Bulk IN 0x81 (passive) ===")
    got_bulk = False
    for i in range(5):
        try:
            data = dev.read(0x81, 4096, timeout=500)
            print(f"  BULK [{i}]: {len(data)} bytes: {bytes(data[:64]).hex()}")
            got_bulk = True
        except usb.core.USBTimeoutError:
            pass
    if not got_bulk:
        print("  No bulk data (5 × 500ms)")

    # 3. SET_CONTROL_LINE_STATE — DTR=1, RTS=1
    #    CDC ACM class request: bmRequestType=0x21, bRequest=0x22
    print("\n=== 3. SET_CONTROL_LINE_STATE (DTR+RTS on) ===")
    dev.ctrl_transfer(0x21, 0x22, 0x0003, 0, b"")
    time.sleep(0.5)
    for i in range(5):
        try:
            data = dev.read(0x81, 4096, timeout=500)
            print(f"  After DTR [{i}]: {len(data)} bytes: {bytes(data[:64]).hex()}")
            got_bulk = True
        except usb.core.USBTimeoutError:
            pass
    if not got_bulk:
        print("  Still no data after DTR assert")

    # 4. SET_LINE_CODING — try 921600 baud
    print("\n=== 4. SET_LINE_CODING (921600 8N1) ===")
    line_coding = struct.pack("<IBBB", 921600, 0, 0, 8)
    dev.ctrl_transfer(0x21, 0x20, 0, 0, line_coding)
    time.sleep(0.5)
    for i in range(5):
        try:
            data = dev.read(0x81, 4096, timeout=500)
            print(f"  After LINE_CODING [{i}]: {len(data)} bytes: {bytes(data[:64]).hex()}")
        except usb.core.USBTimeoutError:
            pass
    else:
        print("  Still no data after SET_LINE_CODING")

    # 5. Write probes via bulk OUT 0x02, then read
    print("\n=== 5. Write probes (bulk OUT 0x02 → read IN 0x81) ===")
    probes = [
        b"ID;",
        b"\x00",
        b"\xff\x01\xee\x01",
        b"INIT\r\n",
        b"\x01",
        b";\r",
        b"?",
    ]
    for probe in probes:
        try:
            dev.write(0x02, probe, timeout=500)
            time.sleep(0.3)
            data = dev.read(0x81, 4096, timeout=500)
            print(f"  {probe!r:25s} → {len(data)} bytes: {bytes(data[:32]).hex()}")
        except usb.core.USBTimeoutError:
            pass
        except usb.core.USBError as e:
            print(f"  {probe!r:25s} → error: {e}")

    print("  (no responses)" if not got_bulk else "")

    # 6. GET_LINE_CODING — read back what device thinks
    print("\n=== 6. GET_LINE_CODING (read device config) ===")
    try:
        ret = dev.ctrl_transfer(0xA1, 0x21, 0, 0, 7, timeout=500)
        baud, stop, parity, bits = struct.unpack("<IBBB", bytes(ret))
        print(f"  Baud={baud} Stop={stop} Parity={parity} Bits={bits}")
    except Exception as e:
        print(f"  Error: {e}")

    # Cleanup: reattach kernel driver
    print("\n=== Cleanup ===")
    usb.util.dispose_resources(dev)
    for intf in [0, 1]:
        try:
            dev.attach_kernel_driver(intf)
            print(f"  Reattached kernel driver to IF{intf}")
        except Exception:
            pass

    print("\nDone.")


if __name__ == "__main__":
    main()
