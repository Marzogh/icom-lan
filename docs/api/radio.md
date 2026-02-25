# IcomRadio

The main entry point for controlling an Icom transceiver over LAN.

## Class: `IcomRadio`

```python
from icom_lan import IcomRadio
```

### Constructor

```python
IcomRadio(
    host: str,
    port: int = 50001,
    username: str = "",
    password: str = "",
    radio_addr: int = 0x98,
    timeout: float = 5.0,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | *required* | Radio IP address or hostname |
| `port` | `int` | `50001` | Control port number |
| `username` | `str` | `""` | Authentication username |
| `password` | `str` | `""` | Authentication password |
| `radio_addr` | `int` | `0x98` | CI-V address of the radio |
| `timeout` | `float` | `5.0` | Default timeout for all operations (seconds) |

### Context Manager

`IcomRadio` supports `async with` for automatic connection management:

```python
async with IcomRadio("192.168.1.100", username="u", password="p") as radio:
    freq = await radio.get_frequency()
# Disconnect happens automatically
```

Equivalent to:

```python
radio = IcomRadio("192.168.1.100", username="u", password="p")
await radio.connect()
try:
    freq = await radio.get_frequency()
finally:
    await radio.disconnect()
```

---

## Properties

### `connected`

```python
@property
def connected(self) -> bool
```

Whether the radio is currently connected and ready for commands.

---

## Connection Methods

### `connect()`

```python
async def connect(self) -> None
```

Open connection to the radio and authenticate. Performs the full handshake:

1. Discovery (Are You There → I Am Here)
2. Login with credentials
3. Token acknowledgement
4. Conninfo exchange
5. CI-V data stream open

**Raises:**

| Exception | When |
|-----------|------|
| `ConnectionError` | UDP connection failed |
| `AuthenticationError` | Login rejected |
| `TimeoutError` | Radio didn't respond |

### `disconnect()`

```python
async def disconnect(self) -> None
```

Cleanly disconnect from the radio. Closes the CI-V data stream and both UDP connections.

---

## Frequency

### `get_frequency()`

```python
async def get_frequency(self) -> int
```

Get the current operating frequency in **Hz**.

**Returns:** `int` — frequency in Hz (e.g., `14074000`)

### `set_frequency()`

```python
async def set_frequency(self, freq_hz: int) -> None
```

Set the operating frequency.

| Parameter | Type | Description |
|-----------|------|-------------|
| `freq_hz` | `int` | Frequency in Hz |

**Raises:** `CommandError` if the radio rejects the frequency.

---

## Mode

### `get_mode()`

```python
async def get_mode(self) -> Mode
```

Get the current operating mode.

**Returns:** `Mode` enum value (e.g., `Mode.USB`)

### `set_mode()`

```python
async def set_mode(self, mode: Mode | str) -> None
```

Set the operating mode.

| Parameter | Type | Description |
|-----------|------|-------------|
| `mode` | `Mode \| str` | Mode enum or name string (`"USB"`, `"CW"`, etc.) |

**Raises:** `CommandError` if the radio rejects the mode.

---

## Power

### `get_power()`

```python
async def get_power(self) -> int
```

Get the RF power level.

**Returns:** `int` — power level (0–255)

### `set_power()`

```python
async def set_power(self, level: int) -> None
```

Set the RF power level.

| Parameter | Type | Description |
|-----------|------|-------------|
| `level` | `int` | Power level 0–255 |

---

## Meters

### `get_s_meter()`

```python
async def get_s_meter(self) -> int
```

Read the S-meter value. **Returns:** `int` (0–255)

### `get_swr()`

```python
async def get_swr(self) -> int
```

Read the SWR meter value (TX only). **Returns:** `int` (0–255)

**Raises:** `TimeoutError` if not transmitting.

### `get_alc()`

```python
async def get_alc(self) -> int
```

Read the ALC meter value (TX only). **Returns:** `int` (0–255)

**Raises:** `TimeoutError` if not transmitting.

---

## PTT

### `set_ptt()`

```python
async def set_ptt(self, on: bool) -> None
```

Toggle Push-To-Talk.

| Parameter | Type | Description |
|-----------|------|-------------|
| `on` | `bool` | `True` = TX, `False` = RX |

---

## VFO & Split

### `select_vfo()`

```python
async def select_vfo(self, vfo: str = "A") -> None
```

Select the active VFO.

| Value | Description |
|-------|-------------|
| `"A"` | VFO A |
| `"B"` | VFO B |
| `"MAIN"` | Main receiver (IC-7610) |
| `"SUB"` | Sub receiver (IC-7610) |

### `vfo_equalize()`

```python
async def vfo_equalize(self) -> None
```

Copy VFO A settings to VFO B (A=B).

### `vfo_exchange()`

```python
async def vfo_exchange(self) -> None
```

Swap VFO A and VFO B.

### `set_split_mode()`

```python
async def set_split_mode(self, on: bool) -> None
```

Enable or disable split mode (TX on VFO B, RX on VFO A).

---

## Attenuator & Preamp

### `set_attenuator()`

```python
async def set_attenuator(self, on: bool) -> None
```

Enable or disable the attenuator.

### `set_preamp()`

```python
async def set_preamp(self, level: int = 1) -> None
```

Set the preamp level.

| Level | Description |
|-------|-------------|
| `0` | Off |
| `1` | PREAMP 1 |
| `2` | PREAMP 2 |

---

## CW

### `send_cw_text()`

```python
async def send_cw_text(self, text: str) -> None
```

Send CW text via the radio's built-in keyer. Long messages are automatically split into 30-character chunks.

### `stop_cw_text()`

```python
async def stop_cw_text(self) -> None
```

Stop CW sending in progress.

---

## Power Control

### `power_control()`

```python
async def power_control(self, on: bool) -> None
```

Remote power on/off. Requires the radio to maintain network connectivity in standby.

---

## Raw CI-V

### `send_civ()`

```python
async def send_civ(
    self,
    command: int,
    sub: int | None = None,
    data: bytes | None = None,
) -> CivFrame
```

Send an arbitrary CI-V command and return the response.

| Parameter | Type | Description |
|-----------|------|-------------|
| `command` | `int` | CI-V command byte |
| `sub` | `int \| None` | Optional sub-command byte |
| `data` | `bytes \| None` | Optional payload data |

**Returns:** `CivFrame` with the radio's response.
