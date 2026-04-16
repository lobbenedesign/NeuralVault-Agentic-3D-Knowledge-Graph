"""
neuralvault.storage.aobf
────────────────────────────
Implementation of the Zero-Waste Append-Only Binary Format (AOBF) 
using Fixed-Size Memory-Mapped Ring Buffers for high-frequency telemetry.
"""

import os
import mmap
import struct
import time
import xxhash
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterator, List

# ============================================================================
# CORE: CIRCULAR BUFFER JOURNAL
# ============================================================================

@dataclass
class TelemetryEntry:
    """Minimal overhead journal entry for Agent Telemetry and Signals"""
    sender_id: str         # UUID or Name
    role: str              # Agent Role
    msg: str               # Message or Action
    signal_type: str       # Signal category
    urgency: float         # 0.0-1.0
    timestamp: float       # Epoch
    payload: dict          # Flexible metadata (JSON-like)

    def to_bytes(self) -> bytes:
        """Serialize to a compact binary frame"""
        # Encode strings
        sender_bytes = self.sender_id.encode('utf-8')
        role_bytes = self.role.encode('utf-8')
        msg_bytes = self.msg.encode('utf-8')
        sig_bytes = self.signal_type.encode('utf-8')
        
        # Serialize payload as simple msgpack or json (here we use simple format)
        import json
        payload_bytes = json.dumps(self.payload).encode('utf-8')

        # Frame structure: 
        # [timestamp(d) | urgency(f) | s_len(B) | r_len(B) | sig_len(B) | p_len(I) | data...]
        header = struct.pack(
            '<dfBBBI',
            self.timestamp,
            self.urgency,
            len(sender_bytes),
            len(role_bytes),
            len(sig_bytes),
            len(payload_bytes)
        )
        
        # Note: msg length is inferred from frame size if needed, but we include it in the data block
        msg_len = struct.pack('<I', len(msg_bytes))
        
        frame = header + msg_len + sender_bytes + role_bytes + sig_bytes + payload_bytes + msg_bytes
        
        # Checksum (xxhash64)
        checksum = xxhash.xxh64(frame).intdigest() & 0xFFFFFFFFFFFFFFFF
        
        return frame + struct.pack('<Q', checksum)

    @staticmethod
    def from_bytes(data: bytes) -> 'TelemetryEntry':
        """Deserialize from binary with integrity check"""
        # Header (20 bytes)
        ts, urg, s_len, r_len, sig_len, p_len = struct.unpack('<dfBBBI', data[:19])
        
        # Msg len (4 bytes)
        msg_len = struct.unpack('<I', data[19:23])[0]
        
        offset = 23
        sender = data[offset:offset+s_len].decode('utf-8')
        offset += s_len
        role = data[offset:offset+r_len].decode('utf-8')
        offset += r_len
        sig = data[offset:offset+sig_len].decode('utf-8')
        offset += sig_len
        import json
        payload = json.loads(data[offset:offset+p_len].decode('utf-8'))
        offset += p_len
        msg = data[offset:offset+msg_len].decode('utf-8')
        offset += msg_len
        
        # Checksum check
        stored_checksum = struct.unpack('<Q', data[offset:offset+8])[0]
        frame = data[:offset]
        expected_checksum = xxhash.xxh64(frame).intdigest() & 0xFFFFFFFFFFFFFFFF
        
        if stored_checksum != expected_checksum:
            raise ValueError(f"Telemetry integrity corrupted: {stored_checksum} != {expected_checksum}")
            
        return TelemetryEntry(sender, role, msg, sig, urg, ts, payload)


class RingBufferJournal:
    """
    Fixed-size, mmap-backed circular buffer for agent signals.
    Guarantees zero-waste disk usage and O(1) writes.
    """
    HEADER_SIZE = 256  # Reserve bytes for metadata (head, tail, etc.)
    
    def __init__(self, file_path: Path | str, max_size_mb: int = 64):
        self.file_path = Path(file_path)
        self.max_size = max_size_mb * 1024 * 1024
        self._mmap = None
        self._file = None
        self.head = self.HEADER_SIZE
        self.tail = self.HEADER_SIZE
        
        self._initialize_storage()

    def _initialize_storage(self):
        """Pre-allocate file and map to memory"""
        if not self.file_path.exists():
            # Create a sparse-ready file
            with open(self.file_path, "wb") as f:
                f.seek(self.max_size - 1)
                f.write(b"\0")
        
        self._file = open(self.file_path, "r+b")
        self._mmap = mmap.mmap(self._file.fileno(), self.max_size)
        
        # Load metadata
        header = self._mmap[:32]
        if header != b"\x00" * 32:
            self.head, self.tail = struct.unpack('<QQ', header[:16])
        else:
            self._update_header()

    def _update_header(self):
        """Sync head/tail pointers to the file header"""
        header_data = struct.pack('<QQ', self.head, self.tail)
        self._mmap[0:16] = header_data
        # We don't always need to flush to disk for every op (performance)
        # but the mmap handles the OS-level paging.

    def append(self, entry: TelemetryEntry):
        """Append an entry, wrapping around if necessary"""
        data = entry.to_bytes()
        frame_len = len(data)
        total_len = frame_len + 4 # 4 bytes for the frame size prefix
        
        # Check for wrap-around
        if self.head + total_len > self.max_size:
            self.head = self.HEADER_SIZE # Reset to start (circular)
            
        # Write Frame Size
        offset = self.head
        self._mmap[offset : offset + 4] = struct.pack('<I', frame_len)
        # Write Data
        self._mmap[offset + 4 : offset + 4 + frame_len] = data
        
        # Update head
        self.head += total_len
        self._update_header()

    def iterate_recent(self, limit: int = 50) -> Iterator[TelemetryEntry]:
        """Iterate backwards from head to get recent entries"""
        # This is a simplified linear iteration. In a real ring buffer,
        # we'd handle the wrap-around more complexly.
        # For now, we just scan back from the current head.
        
        entries = []
        pos = self.tail
        
        # Since it's a ring buffer, we might want to just get the last N
        # We'll do a simple sweep for now.
        while pos < self.head:
            try:
                frame_len = struct.unpack('<I', self._mmap[pos : pos + 4])[0]
                if frame_len == 0 or frame_len > 1024 * 1024: break # Safety break
                
                data = self._mmap[pos + 4 : pos + 4 + frame_len]
                entry = TelemetryEntry.from_bytes(data)
                entries.append(entry)
                pos += 4 + frame_len
            except:
                break
                
        # Return last N
        return reversed(entries[-limit:])

    def close(self):
        self._update_header()
        if self._mmap:
            self._mmap.close()
        if self._file:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
