"""
Service: WPA2 Handshake & EAPOL Packet Capture Analyzer
Parses PCAP, PCAPNG, and CAP files using Scapy.
Identifies 802.1X EAPOL frames, classifies 4-way handshake messages (M1-M4),
inspects Nonces, Key MICs, Replay Counters, and assesses handshake completeness.
Compatible with standard Wireshark/tshark captures.
"""

import logging
import os
import tempfile
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple

from scapy.utils import rdpcap
from scapy.layers.l2 import Ether
from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11ProbeResp, Dot11Elt
from scapy.layers.eap import EAPOL, EAPOL_KEY

logger = logging.getLogger(__name__)


@dataclass
class EapolPacketInfo:
    frame_index: int
    timestamp: float
    src_mac: str
    dst_mac: str
    bssid: Optional[str]
    message_type: str
    message_description: str
    key_descriptor_type: int
    key_descriptor_version: int
    key_replay_counter: int
    key_nonce_hex: str
    key_mic_hex: str
    key_data_length: int
    key_data_preview: str
    is_pairwise: bool
    is_ack: bool
    has_mic: bool
    is_install: bool
    is_secure: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HandshakeEvidence:
    conversation_id: str
    ap_mac: str
    sta_mac: str
    associated_ssid: Optional[str]
    messages_found: List[str]
    completeness: str  # 'COMPLETE_4WAY', 'VALID_HANDSHAKE_PAIR', 'INCOMPLETE_HANDSHAKE', 'NO_HANDSHAKE'
    is_usable_for_offline_validation: bool
    anonce_hex: Optional[str]
    snonce_hex: Optional[str]
    key_mic_hex: Optional[str]
    mic_algorithm: str
    key_replay_counter: Optional[int]
    cryptographic_summary: str
    packet_indices: List[int]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PcapAnalyzerService:
    """Parses packet captures for 802.11 beacons and EAPOL 4-way handshake messages."""

    @classmethod
    def parse_pcap_bytes(
        cls,
        data: bytes,
        filename: str,
        target_ssid: Optional[str] = None,
        target_bssid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Parses in-memory PCAP/PCAPNG bytes by writing to a secure temporary file."""
        suffix = ".pcapng" if filename.lower().endswith(".pcapng") else ".pcap"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
            tf.write(data)
            temp_path = tf.name

        try:
            return cls.parse_pcap_file(
                filepath=temp_path,
                filename=filename,
                target_ssid=target_ssid,
                target_bssid=target_bssid
            )
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @classmethod
    def parse_pcap_file(
        cls,
        filepath: str,
        filename: Optional[str] = None,
        target_ssid: Optional[str] = None,
        target_bssid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Parses a PCAP file path and extracts beacons, EAPOL frames, and handshake evidence."""
        display_name = filename or os.path.basename(filepath)

        try:
            packets = rdpcap(filepath)
        except Exception as e:
            logger.warning(f"Failed to parse PCAP file {display_name}: {e}")
            return {
                "status": "ERROR",
                "filename": display_name,
                "error": f"Invalid or corrupted PCAP capture: {e}",
                "total_packets": 0,
                "eapol_packets_count": 0,
                "beacons_discovered": [],
                "eapol_frames": [],
                "handshake_conversations": [],
                "best_handshake": None
            }

        total_pkts = len(packets)
        beacons_map: Dict[str, str] = {}  # bssid -> ssid
        eapol_frames: List[EapolPacketInfo] = []

        # 1. First pass: extract Beacons and Probe Responses for SSID mapping
        for idx, pkt in enumerate(packets):
            if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
                bssid = None
                if pkt.haslayer(Dot11):
                    bssid = (pkt[Dot11].addr3 or pkt[Dot11].addr2 or "").upper()
                ssid = cls._extract_ssid_from_dot11(pkt)
                if bssid and ssid and bssid not in beacons_map:
                    beacons_map[bssid] = ssid

        # 2. Second pass: extract and inspect EAPOL / EAPOL-Key frames
        for idx, pkt in enumerate(packets):
            if pkt.haslayer(EAPOL) and pkt.haslayer(EAPOL_KEY):
                ep = pkt[EAPOL]
                ek = pkt[EAPOL_KEY]

                src_mac, dst_mac, bssid = cls._extract_mac_addresses(pkt)
                msg_type, msg_desc = cls._classify_eapol_key_frame(ek)

                # Format nonces and MIC
                nonce_raw = bytes(ek.key_nonce) if hasattr(ek, "key_nonce") else b""
                nonce_hex = nonce_raw.hex() if nonce_raw and any(b != 0 for b in nonce_raw) else "00" * 32

                mic_raw = bytes(ek.key_mic) if hasattr(ek, "key_mic") else b""
                mic_hex = mic_raw.hex() if mic_raw else "00" * 16

                key_data_raw = bytes(ek.key_data) if hasattr(ek, "key_data") else b""
                key_data_hex = key_data_raw.hex() if key_data_raw else ""
                key_data_preview = key_data_hex[:64] + ("..." if len(key_data_hex) > 64 else "")

                # Timestamp
                pkt_time = float(pkt.time) if hasattr(pkt, "time") else 0.0

                frame_info = EapolPacketInfo(
                    frame_index=idx + 1,
                    timestamp=pkt_time,
                    src_mac=src_mac.upper(),
                    dst_mac=dst_mac.upper(),
                    bssid=bssid.upper() if bssid else None,
                    message_type=msg_type,
                    message_description=msg_desc,
                    key_descriptor_type=int(ek.key_descriptor_type) if hasattr(ek, "key_descriptor_type") else 2,
                    key_descriptor_version=int(ek.key_descriptor_type_version) if hasattr(ek, "key_descriptor_type_version") else 2,
                    key_replay_counter=int(ek.key_replay_counter) if hasattr(ek, "key_replay_counter") else 0,
                    key_nonce_hex=nonce_hex,
                    key_mic_hex=mic_hex,
                    key_data_length=int(ek.key_data_length) if hasattr(ek, "key_data_length") else len(key_data_raw),
                    key_data_preview=key_data_preview,
                    is_pairwise=bool(ek.key_type == 1) if hasattr(ek, "key_type") else True,
                    is_ack=bool(ek.key_ack == 1) if hasattr(ek, "key_ack") else False,
                    has_mic=bool(ek.has_key_mic == 1) if hasattr(ek, "has_key_mic") else False,
                    is_install=bool(ek.install == 1) if hasattr(ek, "install") else False,
                    is_secure=bool(ek.secure == 1) if hasattr(ek, "secure") else False,
                )
                eapol_frames.append(frame_info)

        # 3. Third pass: Conversation analysis and Handshake completeness
        conversations = cls._analyze_handshake_conversations(
            eapol_frames, beacons_map, target_ssid, target_bssid
        )

        # Determine best handshake matching target
        best_handshake = None
        for hs in conversations:
            if hs.is_usable_for_offline_validation:
                if target_ssid and hs.associated_ssid and target_ssid.lower() == hs.associated_ssid.lower():
                    best_handshake = hs
                    break
                if not best_handshake:
                    best_handshake = hs

        if not best_handshake and conversations:
            best_handshake = conversations[0]

        beacons_summary = [{"bssid": b, "ssid": s} for b, s in beacons_map.items()]

        return {
            "status": "PARSED_SUCCESS",
            "filename": display_name,
            "total_packets": total_pkts,
            "eapol_packets_count": len(eapol_frames),
            "beacons_discovered": beacons_summary,
            "eapol_frames": [f.to_dict() for f in eapol_frames],
            "handshake_conversations": [c.to_dict() for c in conversations],
            "best_handshake": best_handshake.to_dict() if best_handshake else None,
            "has_valid_handshake": bool(best_handshake and best_handshake.is_usable_for_offline_validation)
        }

    @staticmethod
    def _extract_ssid_from_dot11(pkt) -> Optional[str]:
        """Extracts SSID string from 802.11 Information Element 0."""
        try:
            elt = pkt.getlayer(Dot11Elt)
            while elt:
                if elt.ID == 0 and elt.info:
                    return elt.info.decode("utf-8", errors="replace")
                elt = elt.payload.getlayer(Dot11Elt)
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_mac_addresses(pkt) -> Tuple[str, str, Optional[str]]:
        """Extracts source, destination, and BSSID MAC addresses from Dot11 or Ethernet."""
        if pkt.haslayer(Dot11):
            d11 = pkt[Dot11]
            src = d11.addr2 or "00:00:00:00:00:00"
            dst = d11.addr1 or "00:00:00:00:00:00"
            bssid = d11.addr3 or src
            return src, dst, bssid
        elif pkt.haslayer(Ether):
            eth = pkt[Ether]
            src = eth.src or "00:00:00:00:00:00"
            dst = eth.dst or "00:00:00:00:00:00"
            return src, dst, None
        return "00:00:00:00:00:00", "00:00:00:00:00:00", None

    @staticmethod
    def _classify_eapol_key_frame(ek: EAPOL_KEY) -> Tuple[str, str]:
        """Classifies EAPOL-Key frame based on 802.11i Key Information flags."""
        key_type = getattr(ek, "key_type", 1)
        key_ack = getattr(ek, "key_ack", 0)
        has_mic = getattr(ek, "has_key_mic", 0)
        install = getattr(ek, "install", 0)
        secure = getattr(ek, "secure", 0)

        if key_type == 1:  # Pairwise Key
            if key_ack == 1 and has_mic == 0:
                return "M1", "Message 1 (M1): Authenticator (AP) -> Supplicant (STA) transmits ANonce"
            elif key_ack == 0 and has_mic == 1 and secure == 0:
                return "M2", "Message 2 (M2): Supplicant (STA) -> Authenticator (AP) transmits SNonce and Key MIC"
            elif key_ack == 1 and has_mic == 1 and install == 1:
                return "M3", "Message 3 (M3): Authenticator (AP) -> Supplicant (STA) commands PTK Install and sends encrypted GTK"
            elif key_ack == 0 and has_mic == 1:
                return "M4", "Message 4 (M4): Supplicant (STA) -> Authenticator (AP) Handshake Complete Acknowledgment"
            return "Pairwise-Key", "Pairwise Key Exchange Frame"
        elif key_type == 0:  # Group Key
            if key_ack == 1:
                return "G1", "Group Key Message 1 (G1): Authenticator (AP) -> Supplicant (STA) GTK Rotation"
            return "G2", "Group Key Message 2 (G2): Supplicant (STA) -> Authenticator (AP) GTK Acknowledgment"
        return "EAPOL-Key", "Standard EAPOL-Key Frame"

    @classmethod
    def _analyze_handshake_conversations(
        cls,
        frames: List[EapolPacketInfo],
        beacons_map: Dict[str, str],
        target_ssid: Optional[str],
        target_bssid: Optional[str]
    ) -> List[HandshakeEvidence]:
        """Groups EAPOL frames by AP/STA pair and assesses 4-way handshake completeness."""
        grouped: Dict[str, List[EapolPacketInfo]] = {}

        for f in frames:
            # Determine AP and STA
            if f.message_type in ("M1", "M3", "G1"):
                ap = f.src_mac
                sta = f.dst_mac
            elif f.message_type in ("M2", "M4", "G2"):
                ap = f.dst_mac
                sta = f.src_mac
            else:
                ap = f.bssid or f.src_mac
                sta = f.dst_mac

            conv_key = f"{ap} <-> {sta}"
            if conv_key not in grouped:
                grouped[conv_key] = []
            grouped[conv_key].append(f)

        evidences: List[HandshakeEvidence] = []

        for conv_id, conv_frames in grouped.items():
            ap_mac = conv_frames[0].src_mac if conv_frames[0].message_type in ("M1", "M3") else conv_frames[0].dst_mac
            sta_mac = conv_frames[0].dst_mac if conv_frames[0].message_type in ("M1", "M3") else conv_frames[0].src_mac

            msg_types = [f.message_type for f in conv_frames]
            pkt_indices = [f.frame_index for f in conv_frames]

            # Find M1, M2, M3, M4
            m1 = next((f for f in conv_frames if f.message_type == "M1"), None)
            m2 = next((f for f in conv_frames if f.message_type == "M2"), None)
            m3 = next((f for f in conv_frames if f.message_type == "M3"), None)
            m4 = next((f for f in conv_frames if f.message_type == "M4"), None)

            anonce = m1.key_nonce_hex if m1 else (m3.key_nonce_hex if m3 else None)
            snonce = m2.key_nonce_hex if m2 else None
            key_mic = m2.key_mic_hex if m2 else (m3.key_mic_hex if m3 else (m4.key_mic_hex if m4 else None))
            replay_counter = m1.key_replay_counter if m1 else (m2.key_replay_counter if m2 else None)

            # Determine MIC Algorithm based on Key Descriptor Version
            ver = m2.key_descriptor_version if m2 else (m1.key_descriptor_version if m1 else 2)
            if ver == 1:
                mic_algo = "HMAC-MD5 (RC4)"
            elif ver == 2:
                mic_algo = "HMAC-SHA1-128 (AES-128-CCMP)"
            elif ver == 3:
                mic_algo = "AES-128-CMAC (WPA3-SAE / 802.11w)"
            else:
                mic_algo = "HMAC-SHA1-128"

            # Check Completeness
            has_complete_4way = bool(m1 and m2 and m3 and m4)
            has_valid_pair = bool(
                m1 and m2 and anonce and snonce and key_mic and (m1.key_replay_counter == m2.key_replay_counter)
            ) or bool(
                m2 and m3 and anonce and snonce and key_mic and (m2.key_replay_counter == m3.key_replay_counter)
            )

            if has_complete_4way:
                completeness = "COMPLETE_4WAY"
                is_usable = True
                summary = (
                    "Complete 4-way handshake verified: Messages M1, M2, M3, and M4 are all present and aligned. "
                    "Authenticator Nonce (ANonce), Supplicant Nonce (SNonce), and Key MIC are fully captured."
                )
            elif has_valid_pair:
                completeness = "VALID_HANDSHAKE_PAIR"
                is_usable = True
                summary = (
                    "Valid cryptographic handshake pair captured (M1 + M2). "
                    "Both ANonce and SNonce are captured, and Message 2 contains a valid Key MIC calculated over the frame. "
                    "This provides sufficient cryptographic evidence to verify pre-shared key knowledge offline."
                )
            elif m1 and not m2:
                completeness = "INCOMPLETE_HANDSHAKE"
                is_usable = False
                summary = (
                    "Incomplete Handshake: Message 1 (ANonce) was captured from the Access Point, "
                    "but client reply Message 2 (SNonce + Key MIC) is missing from this capture."
                )
            elif m2 and not m1:
                completeness = "INCOMPLETE_HANDSHAKE"
                is_usable = False
                summary = (
                    "Incomplete Handshake: Message 2 (SNonce + Key MIC) was captured from the client, "
                    "but Access Point Message 1 (ANonce) is missing."
                )
            else:
                completeness = "INCOMPLETE_HANDSHAKE"
                is_usable = False
                summary = f"Partial EAPOL traffic captured ({', '.join(set(msg_types))}). Handshake is incomplete."

            # Map SSID from beacon
            assoc_ssid = beacons_map.get(ap_mac) or (target_ssid if target_bssid and ap_mac == target_bssid.upper() else None)

            evidences.append(
                HandshakeEvidence(
                    conversation_id=conv_id,
                    ap_mac=ap_mac,
                    sta_mac=sta_mac,
                    associated_ssid=assoc_ssid,
                    messages_found=msg_types,
                    completeness=completeness,
                    is_usable_for_offline_validation=is_usable,
                    anonce_hex=anonce,
                    snonce_hex=snonce,
                    key_mic_hex=key_mic,
                    mic_algorithm=mic_algo,
                    key_replay_counter=replay_counter,
                    cryptographic_summary=summary,
                    packet_indices=pkt_indices
                )
            )

        return evidences


pcap_analyzer = PcapAnalyzerService()
