"""Scan sequence D5, D8, E9, D4, C2, 03, (E0, 28 reads, 28 info, C2)*, D6 on the scan channel; EE after a
double feed.

Flow and parameter blocks: docs/protocol-ix1500.md, section "Scan sequence".
"""

from __future__ import annotations

import contextlib
import struct
from collections.abc import Iterator

from ...core.errors import FeedError, NoPaper
from ...core.model import SCAN_HEIGHT_1200, SCAN_WIDTH_1200, ImageInfo, ScanSettings, Sheet
from . import wire
from .scsi import CHECK_CONDITION, ScsiChannel, ScsiError, Sense

# Combinations whose parameter blocks come 1:1 from captures, with the read length from the capture. color/300 is
# from a capture of a profile with automatic color mode and resolution (see _CAPTURED_MODE_BLOCKS).
VERIFIED: dict[tuple[str, int], int] = {("gray", 150): 0x300000, ("color", 600): 0x20000, ("color", 300): 0x300000}

# D4 blocks as ScanSnap Home sent them, where they differ from the derived block. color/300: from the private
# double-feed capture, for a profile with automatic color mode and resolution that delivered a 300 dpi
# 3-channel JPEG.
# UNVERIFIED: the full block for a profile set to color/300 explicitly; bytes 10, 13 and 40 match.
_CAPTURED_MODE_BLOCKS: dict[tuple[str, int], bytes] = {
    ("color", 300): bytes.fromhex(
        "00030101d000c1808080908080000000000000000000000000000000000000300010012c012c05810d00000028d0000044dc04"
    ).ljust(80, b"\0"),
}

_MODE_TEMPLATE = bytes.fromhex(
    "00030101d000c18080808080800000000000000000000000000000000000003000100096009605810500000028d0000044dc04"
).ljust(80, b"\0")


def is_verified(settings: ScanSettings) -> bool:
    return (settings.mode, settings.dpi) in VERIFIED


def read_len(settings: ScanSettings) -> int:
    # UNVERIFIED: 0x20000 for combinations without a capture (taken from color/600)
    return VERIFIED.get((settings.mode, settings.dpi), 0x20000)


def window_block(settings: ScanSettings) -> bytes:
    """E9 data block (32 B)."""
    dpi = settings.dpi
    return (struct.pack(">HHII", dpi, dpi, SCAN_WIDTH_1200, SCAN_HEIGHT_1200) + b"\x05").ljust(32, b"\0")


def mode_block(settings: ScanSettings) -> bytes:
    """D4 data block (80 B)."""
    captured = _CAPTURED_MODE_BLOCKS.get((settings.mode, settings.dpi))
    if captured:
        return captured
    # UNVERIFIED: derived except for gray/150, color/300 and color/600 (byte 13 color, 34–37 dpi, 40 mode).
    b = bytearray(_MODE_TEMPLATE)
    b[13] = 0x80 if settings.mode == "color" else 0x00
    struct.pack_into(">HH", b, 34, settings.dpi, settings.dpi)
    b[40] = 0x0A if settings.mode == "color" else 0x05
    return bytes(b)


def parse_image_info(d: bytes) -> ImageInfo:
    w, hmax, _w2, h, dx, dy = struct.unpack_from(">IIIIHH", d)
    return ImageInfo(w, hmax, h, dx, dy)


def double_feed(status: bytes) -> int | None:
    """The error code (byte 7) if a C2 status block reports a double feed (byte 6 bit 0), else None.

    With a double feed the sheet's reads end with the normal EOM sense, and C2 afterwards shows the fault.
    Crumpled single sheets set the same flag (session capture).
    """
    # UNVERIFIED: byte 7 has only been seen as 0 or 0x55 (double feed); other codes are not acted on.
    if len(status) < 8 or not status[6] & 0x01:
        return None
    return status[7]


def _ack_cdb() -> bytes:
    return bytes.fromhex("ee0000000800")


def _sense_error(msg: str, sense: Sense) -> Exception:
    reason = sense.medium_error
    return FeedError(reason, str(sense)) if reason else ScsiError(msg, sense)


def _read_cdb(side: int, chunk: int, length: int) -> bytes:
    return bytes([0x28, 0, 0, 2, 0, 0x80 if side else 0]) + length.to_bytes(3, "big") + bytes([0, side, chunk])


def _info_cdb(side: int) -> bytes:
    return bytes([0x28, 0, 0x80, 0, 0, 0x80 if side else 0, 0, 0, 0x20, 0, side, 0])


class Scanner:
    """Scan sequence on an open scan channel."""

    def __init__(self, channel: ScsiChannel):
        self.ch = channel

    def _read_page(self, read_len: int) -> tuple[list[bytes], int]:
        parts: list[list[bytes]] = [[], []]
        done = [False, False]
        chunk = [0, 0]
        last = 0
        while not all(done):
            for side in (0, 1):
                if done[side]:
                    continue
                r = self.ch.command(_read_cdb(side, chunk[side], read_len), in_len=read_len)
                # The sense comes first: when a sheet jams, the read ends with CHECK CONDITION and data that
                # is not an image chunk (private session capture), so the chunk header says nothing.
                sense = self.ch.request_sense() if r.status == CHECK_CONDITION else None
                if sense is not None and not sense.eom:
                    raise _sense_error("read failed", sense)
                if r.status and sense is None:
                    raise ScsiError(f"read status {r.status}")
                if r.data[:2] != bytes([side, chunk[side]]):
                    raise ScsiError(f"unexpected chunk header {r.data[:2].hex()} for side {side}")
                parts[side].append(r.data[2:])
                chunk[side] += 1
                if sense is not None:
                    done[side], last = True, side
        return [b"".join(p) for p in parts], last

    def scan(self, settings: ScanSettings) -> Iterator[Sheet]:
        """Scans all sheets in the feeder. Raises NoPaper if the feeder is empty."""
        ch = self.ch
        ch.checked(bytes.fromhex("d50000010808"), out=b"\0" * 8, in_len=8)
        released = False
        try:
            ch.checked(bytes.fromhex("d80000000000"))
            ch.checked(bytes.fromhex("e9000000000000200000"), out=window_block(settings))
            ch.checked(bytes.fromhex("d40000005000"), out=mode_block(settings))
            # Like ScanSnap Home: C2 once after D4. A double-feed flag from an earlier batch stays set until the
            # next batch starts; here it was clear in every capture.
            ch.hardware_status()
            ch.request_sense()
            pages = 0
            while True:
                r = ch.command(bytes.fromhex("e00000000000"))
                if r.status == CHECK_CONDITION:
                    sense = ch.request_sense()
                    if sense.no_paper:
                        if pages == 0:
                            raise NoPaper("no paper in feeder")
                        return
                    raise _sense_error("feed failed", sense)
                (front, back), last = self._read_page(read_len(settings))
                info = parse_image_info(ch.checked(_info_cdb(last), in_len=0x20).data)
                # Like ScanSnap Home: C2 after the sheet's image info, where a double feed shows up.
                code = double_feed(ch.hardware_status())
                if code is not None:
                    # ScanSnap Home then sends EE with 8 bytes (00 00 00 55 00 00 00 00), then D8, and the panel
                    # asks the user whether to continue. Here the batch stops; the sheet is not delivered.
                    # UNVERIFIED: how the panel's "continue" reaches the host.
                    # UNVERIFIED: the EE data layout (u32 error code, u32 0), from one sample.
                    # UNVERIFIED: whether the next E0 would report a sense for the double feed.
                    # UNVERIFIED: the meaning of C2 byte 2 bit 7, set after jams and once after a double feed.
                    with contextlib.suppress(OSError, wire.ProtocolError):  # report the double feed regardless
                        ch.command(_ack_cdb(), out=struct.pack(">II", code, 0))
                    raise FeedError("double feed", f"sheet {pages + 1}, error code {code:#04x}")
                pages += 1
                yield Sheet(front, back if settings.duplex else None, info)
        except BaseException:
            # Release the scanner, but report the error that stopped the scan, not a failing D6.
            released = True
            with contextlib.suppress(OSError, wire.ProtocolError):
                ch.command(bytes.fromhex("d60000000000"))
            raise
        finally:
            if not released:
                ch.command(bytes.fromhex("d60000000000"))
