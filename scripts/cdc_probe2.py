#!/usr/bin/env python3
"""FTX-1 CDC probe v2 — SPI-style polling via CDC. Requires sudo."""

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

    for intf in [0, 1]:
        if dev.is_kernel_driver_active(intf):
            dev.detach_kernel_driver(intf)
            print(f"Detached kernel driver from IF{intf}")

    dev.set_configuration()

    # Set line coding to 921600 (matches what device returned)
    line_coding = struct.pack("<IBBB", 921600, 0, 0, 8)
    dev.ctrl_transfer(0x21, 0x20, 0, 0, line_coding)
    # DTR + RTS on
    dev.ctrl_transfer(0x21, 0x22, 0x0003, 0, b"")
    print("Line coding + DTR/RTS set.\n")

    # === Key test: ratmandu sends 'INIT' via SPI to start data flow ===
    # Maybe CDC needs the same trigger

    print("=== Test 1: INIT command (like FT-710 SPI) ===")
    init_variants = [
        b"INIT",           # exact bytes ratmandu sends
        b"INIT\x00",       # null terminated
        b"INIT\r",         # with CR
        b"INIT\r\n",       # with CRLF
        b"INIT;",          # CAT-style
        b"init",           # lowercase
        b"\x00INIT",       # with leading null
    ]

    for init_cmd in init_variants:
        try:
            dev.write(0x02, init_cmd, timeout=500)
            time.sleep(0.2)
            # Try to read 4096 bytes (full SPI packet size)
            data = dev.read(0x81, 4096, timeout=1000)
            print(f"  {init_cmd!r:20s} → {len(data)} bytes!")
            print(f"    First 64: {bytes(data[:64]).hex()}")
            # Check for sync
            raw = bytes(data)
            idx = raw.find(b"\xff\x01\xee\x01")
            if idx >= 0:
                print(f"    SYNC MARKER at offset {idx}!")
        except usb.core.USBTimeoutError:
            pass
        except usb.core.USBError as e:
            print(f"  {init_cmd!r:20s} → error: {e}")

    # === Test 2: SPI-style polling — write empty/short, read 4096 ===
    print("\n=== Test 2: SPI-style poll (write short, read 4096) ===")
    poll_cmds = [
        b"\x00" * 4,       # 4 null bytes (SPI dummy)
        b"\x00" * 4096,    # full frame of nulls (SPI read = write nulls)
        b"\xff" * 4,       # all ones
        b"\x01\x00\x00\x00",  # command byte 1
        b"\x02\x00\x00\x00",  # command byte 2
    ]

    for cmd in poll_cmds:
        try:
            dev.write(0x02, cmd, timeout=500)
            time.sleep(0.1)
            data = dev.read(0x81, 4096, timeout=1000)
            print(f"  {cmd[:8]!r:25s} → {len(data)} bytes!")
            print(f"    First 32: {bytes(data[:32]).hex()}")
        except usb.core.USBTimeoutError:
            pass
        except usb.core.USBError as e:
            print(f"  {cmd[:8]!r:25s} → error: {e}")

    # === Test 3: Two-step like SPI — INIT then poll loop ===
    print("\n=== Test 3: INIT then poll loop ===")
    try:
        dev.write(0x02, b"INIT", timeout=500)
        time.sleep(0.5)

        for i in range(10):
            try:
                # SPI read = write zeros and read response
                dev.write(0x02, b"\x00" * 64, timeout=500)
                time.sleep(0.05)
                data = dev.read(0x81, 4096, timeout=500)
                print(f"  Poll {i}: {len(data)} bytes: {bytes(data[:32]).hex()}")
            except usb.core.USBTimeoutError:
                pass
    except usb.core.USBError as e:
        print(f"  Error: {e}")

    if not any(True for _ in []):  # placeholder
        print("  No data from poll loop")

    # === Test 4: CDC SEND_BREAK (might trigger something) ===
    print("\n=== Test 4: SEND_BREAK ===")
    try:
        # CDC SEND_BREAK: bmRequestType=0x21, bRequest=0x23, wValue=duration
        dev.ctrl_transfer(0x21, 0x23, 100, 0, b"")  # 100ms break
        time.sleep(0.5)
        data = dev.read(0x81, 4096, timeout=1000)
        print(f"  After BREAK: {len(data)} bytes: {bytes(data[:32]).hex()}")
    except usb.core.USBTimeoutError:
        print("  No data after SEND_BREAK")
    except usb.core.USBError as e:
        print(f"  Error: {e}")

    # Cleanup
    print("\n=== Cleanup ===")
    usb.util.dispose_resources(dev)
    for intf in [0, 1]:
        try:
            dev.attach_kernel_driver(intf)
            print(f"  Reattached IF{intf}")
        except Exception:
            pass

    print("\nDone.")


if __name__ == "__main__":
    main()
