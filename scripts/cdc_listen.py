#!/usr/bin/env python3
"""FTX-1 CDC passive listener — runs 30 seconds. Requires sudo.

Turn on GPS / WIRES-X / change scope modes on the radio while this runs.
"""

import struct
import time
import sys

import usb.core
import usb.util

DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 30


def main():
    dev = usb.core.find(idVendor=0x26AA, idProduct=0x0030)
    if not dev:
        print("CDC device (26AA:0030) not found")
        return

    print(f"Found: {dev.manufacturer} {dev.product}")

    for intf in [0, 1]:
        if dev.is_kernel_driver_active(intf):
            dev.detach_kernel_driver(intf)
            print(f"Detached kernel driver from IF{intf}")

    dev.set_configuration()

    # Set up line coding + DTR/RTS
    line_coding = struct.pack("<IBBB", 115200, 0, 0, 8)
    dev.ctrl_transfer(0x21, 0x20, 0, 0, line_coding)
    dev.ctrl_transfer(0x21, 0x22, 0x0003, 0, b"")

    print(f"\nListening on bulk IN + interrupt for {DURATION} seconds...")
    print(">>> Toggle GPS, WIRES-X, scope modes on the radio NOW <<<\n")

    start = time.time()
    bulk_total = 0
    intr_total = 0

    while time.time() - start < DURATION:
        elapsed = time.time() - start

        # Check bulk IN
        try:
            data = dev.read(0x81, 4096, timeout=200)
            bulk_total += len(data)
            raw = bytes(data)
            # Try to detect content type
            preview = raw[:32]
            is_nmea = preview.startswith(b"$G")
            is_ascii = all(0x20 <= b <= 0x7E or b in (0x0D, 0x0A) for b in preview if b != 0)
            
            print(f"  [{elapsed:5.1f}s] BULK: {len(data)} bytes", end="")
            if is_nmea:
                print(f" NMEA! {raw[:80]}")
            elif is_ascii:
                print(f" ASCII: {raw[:60]}")
            else:
                print(f" BIN: {raw[:32].hex()}")
        except usb.core.USBTimeoutError:
            pass

        # Check interrupt
        try:
            data = dev.read(0x83, 16, timeout=50)
            intr_total += len(data)
            print(f"  [{elapsed:5.1f}s] INTR: {bytes(data).hex()}")
        except usb.core.USBTimeoutError:
            pass

    print(f"\n--- Summary ---")
    print(f"Duration: {DURATION}s")
    print(f"Bulk IN: {bulk_total} bytes")
    print(f"Interrupt: {intr_total} bytes")

    if bulk_total == 0 and intr_total == 0:
        print("RESULT: Complete silence. CDC endpoint is inactive.")

    # Cleanup
    usb.util.dispose_resources(dev)
    for intf in [0, 1]:
        try:
            dev.attach_kernel_driver(intf)
        except Exception:
            pass

    print("Done.")


if __name__ == "__main__":
    main()
