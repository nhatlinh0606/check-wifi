"""
Module: Security Auditor Service
Provides offline, educational password security analysis, WPA2/WPA3 password generation,
wordlist quality inspection, and theoretical search-space simulation.
Strictly offline: never connects to networks or tests live authentication.
"""

import math
import re
import secrets
import string
from typing import Dict, List, Optional, Any


COMMON_KEYBOARD_WALKS = [
    "qwerty", "asdfgh", "zxcvbn", "123456", "234567", "345678", "456789", "567890",
    "password", "admin", "welcome", "internet", "wireless", "default"
]


class AuditorService:
    """Offline cryptographic and password security auditing logic."""

    @staticmethod
    def calculate_entropy(password: str) -> float:
        """
        Calculates theoretical password entropy in bits:
        Entropy = L * log2(Pool Size)
        """
        if not password:
            return 0.0

        pool_size = 0
        if re.search(r"[a-z]", password):
            pool_size += 26
        if re.search(r"[A-Z]", password):
            pool_size += 26
        if re.search(r"[0-9]", password):
            pool_size += 10
        if re.search(r"[^a-zA-Z0-9]", password):
            pool_size += 33

        if pool_size == 0:
            return 0.0

        return round(len(password) * math.log2(pool_size), 2)

    @classmethod
    def detect_weak_patterns(cls, password: str) -> List[str]:
        """Identifies common human pattern flaws in passwords."""
        warnings = []
        if not password:
            return ["Password is empty."]

        length = len(password)
        if length < 8:
            warnings.append("Length is under 8 characters (Violates WPA2 minimum standard).")
        elif length < 12:
            warnings.append("Length is under 12 characters (Vulnerable to modern offline attacks).")

        # Pure numeric
        if password.isdigit():
            warnings.append("Contains digits only (Highly susceptible to numeric phone-number/birthday sweeps).")

        # Sequential digits (e.g., 123456, 987654)
        has_sequential = False
        for i in range(len(password) - 2):
            if (
                password[i].isdigit()
                and password[i + 1].isdigit()
                and password[i + 2].isdigit()
            ):
                d1, d2, d3 = int(password[i]), int(password[i + 1]), int(password[i + 2])
                if (d2 == d1 + 1 and d3 == d2 + 1) or (d2 == d1 - 1 and d3 == d2 - 1):
                    has_sequential = True
                    break
        if has_sequential:
            warnings.append("Contains sequential ascending or descending numbers.")

        # Repeated single character (e.g. aaaaaa, 88888888)
        if re.search(r"(.)\1{2,}", password):
            warnings.append("Contains 3 or more repeated consecutive identical characters.")

        # Common keyboard walks and dictionary roots
        pwd_lower = password.lower()
        for walk in COMMON_KEYBOARD_WALKS:
            if walk in pwd_lower:
                warnings.append(f"Contains common dictionary word or keyboard sequence ('{walk}').")
                break

        # Check character variety
        has_lower = bool(re.search(r"[a-z]", password))
        has_upper = bool(re.search(r"[A-Z]", password))
        has_digit = bool(re.search(r"[0-9]", password))
        has_symbol = bool(re.search(r"[^a-zA-Z0-9]", password))

        types_count = sum([has_lower, has_upper, has_digit, has_symbol])
        if types_count <= 1:
            warnings.append("Contains only a single character type (Lacks complexity).")
        elif types_count == 2:
            warnings.append("Uses only two character types (Consider mixing symbols & mixed cases).")

        return warnings

    @classmethod
    def evaluate_password(cls, password: str) -> Dict[str, Any]:
        """Evaluates a single password for strength, entropy, and crack time estimates."""
        entropy = cls.calculate_entropy(password)
        warnings = cls.detect_weak_patterns(password)

        length = len(password)
        has_lower = bool(re.search(r"[a-z]", password))
        has_upper = bool(re.search(r"[A-Z]", password))
        has_digit = bool(re.search(r"[0-9]", password))
        has_symbol = bool(re.search(r"[^a-zA-Z0-9]", password))

        # Strength scoring
        score = 0
        if length >= 8:
            score += 1
        if length >= 12:
            score += 1
        if length >= 16:
            score += 1
        if has_lower and has_upper:
            score += 1
        if has_digit:
            score += 1
        if has_symbol:
            score += 1
        if len(warnings) == 0:
            score += 1
        else:
            score = max(0, score - len(warnings))

        if score <= 1 or length < 8:
            strength = "Very Weak"
            color = "rose"
        elif score <= 3:
            strength = "Weak"
            color = "amber"
        elif score <= 4:
            strength = "Fair"
            color = "yellow"
        elif score <= 5:
            strength = "Strong"
            color = "blue"
        else:
            strength = "Very Strong"
            color = "emerald"

        # Theoretical crack time estimates
        pool_size = (26 if has_lower else 0) + (26 if has_upper else 0) + (10 if has_digit else 0) + (33 if has_symbol else 0)
        total_combinations = math.pow(max(1, pool_size), length) if length > 0 else 0

        def format_time(seconds: float) -> str:
            if seconds < 1:
                return "< 1 second"
            elif seconds < 60:
                return f"{int(seconds)} seconds"
            elif seconds < 3600:
                return f"{int(seconds / 60)} minutes"
            elif seconds < 86400:
                return f"{round(seconds / 3600, 1)} hours"
            elif seconds < 31536000:
                return f"{round(seconds / 86400, 1)} days"
            elif seconds < 31536000 * 100:
                return f"{round(seconds / 31536000, 1)} years"
            elif seconds < 31536000 * 1_000_000:
                return f"{int(seconds / 31536000):,} years"
            else:
                return "Centuries (Computationally Infeasible)"

        # 3 Attack scenarios:
        # A. Online Router Auth Rate-Limited (5 attempts/sec)
        time_online = format_time(total_combinations / 5.0) if total_combinations > 0 else "Instant"
        # B. Offline Standard CPU (10,000 attempts/sec)
        time_offline_cpu = format_time(total_combinations / 10_000.0) if total_combinations > 0 else "Instant"
        # C. High-End GPU Cluster (1,000,000 attempts/sec)
        time_offline_gpu = format_time(total_combinations / 1_000_000.0) if total_combinations > 0 else "Instant"

        recommendations = []
        if length < 12:
            recommendations.append("Increase password length to at least 14-16 characters.")
        if not has_symbol:
            recommendations.append("Include special characters (e.g. !@#$%^&*).")
        if not (has_lower and has_upper):
            recommendations.append("Mix uppercase and lowercase letters.")
        if password.isdigit():
            recommendations.append("Avoid purely numeric keys; combine letters and punctuation.")
        if not recommendations:
            recommendations.append("Excellent password complexity. Suitable for WPA2-Enterprise or WPA3-Personal.")

        return {
            "password_masked": (password[:2] + "*" * (length - 4) + password[-2:]) if length >= 6 else "*" * length,
            "length": length,
            "entropy_bits": entropy,
            "strength": strength,
            "color": color,
            "character_sets": {
                "lowercase": has_lower,
                "uppercase": has_upper,
                "digits": has_digit,
                "symbols": has_symbol,
            },
            "warnings": warnings,
            "recommendations": recommendations,
            "theoretical_combinations": f"{total_combinations:.2e}" if total_combinations > 1e6 else f"{int(total_combinations):,}",
            "crack_time_estimates": {
                "online_router_5_per_sec": time_online,
                "offline_cpu_10k_per_sec": time_offline_cpu,
                "offline_gpu_1m_per_sec": time_offline_gpu,
            }
        }

    @staticmethod
    def generate_password(
        length: int = 16,
        include_upper: bool = True,
        include_lower: bool = True,
        include_digits: bool = True,
        include_symbols: bool = True,
        exclude_ambiguous: bool = True
    ) -> str:
        """Generates a cryptographically strong random WPA2/WPA3 password."""
        # Clamp length to valid Wi-Fi WPA standards (8 to 63 characters)
        length = max(8, min(63, length))

        char_pool = ""
        guaranteed_chars = []

        ambiguous = "il1Lo0O"

        lower_chars = string.ascii_lowercase
        upper_chars = string.ascii_uppercase
        digit_chars = string.digits
        symbol_chars = "!@#$%^&*()-_=+[]{}|;:,.<>?"

        if exclude_ambiguous:
            lower_chars = "".join(c for c in lower_chars if c not in ambiguous)
            upper_chars = "".join(c for c in upper_chars if c not in ambiguous)
            digit_chars = "".join(c for c in digit_chars if c not in ambiguous)

        if include_lower:
            char_pool += lower_chars
            guaranteed_chars.append(secrets.choice(lower_chars))
        if include_upper:
            char_pool += upper_chars
            guaranteed_chars.append(secrets.choice(upper_chars))
        if include_digits:
            char_pool += digit_chars
            guaranteed_chars.append(secrets.choice(digit_chars))
        if include_symbols:
            char_pool += symbol_chars
            guaranteed_chars.append(secrets.choice(symbol_chars))

        # Fallback if all unchecked
        if not char_pool:
            char_pool = string.ascii_letters + string.digits
            guaranteed_chars.append(secrets.choice(char_pool))

        remaining_length = length - len(guaranteed_chars)
        random_chars = [secrets.choice(char_pool) for _ in range(remaining_length)]

        combined = guaranteed_chars + random_chars
        # Cryptographic shuffle
        for i in range(len(combined) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            combined[i], combined[j] = combined[j], combined[i]

        return "".join(combined)

    @classmethod
    def analyze_wordlist_text(cls, text: str, max_entries: int = 1_000_000) -> Dict[str, Any]:
        """Analyzes a wordlist to detect duplicates, weak patterns, length distribution, and entropy."""
        lines = [line.strip() for line in text.splitlines() if line.strip()][:max_entries]
        total_count = len(lines)

        if total_count == 0:
            return {
                "total_entries": 0,
                "unique_entries": 0,
                "duplicate_count": 0,
                "duplicate_rate_pct": 0,
                "avg_length": 0,
                "min_length": 0,
                "max_length": 0,
                "weak_count": 0,
                "pure_numeric_count": 0,
                "sequential_count": 0,
                "sample_weak_entries": [],
                "quality_grade": "N/A"
            }

        unique_set = set()
        duplicate_count = 0
        total_len = 0
        min_len = 99999
        max_len = 0

        pure_numeric = 0
        sequential = 0
        weak_entries = []

        for pwd in lines:
            if pwd in unique_set:
                duplicate_count += 1
            else:
                unique_set.add(pwd)

            l = len(pwd)
            total_len += l
            if l < min_len:
                min_len = l
            if l > max_len:
                max_len = l

            is_numeric = pwd.isdigit()
            if is_numeric:
                pure_numeric += 1

            has_seq = False
            for i in range(len(pwd) - 2):
                if pwd[i].isdigit() and pwd[i + 1].isdigit() and pwd[i + 2].isdigit():
                    d1, d2, d3 = int(pwd[i]), int(pwd[i + 1]), int(pwd[i + 2])
                    if (d2 == d1 + 1 and d3 == d2 + 1) or (d2 == d1 - 1 and d3 == d2 - 1):
                        has_seq = True
                        sequential += 1
                        break

            if (l < 8 or is_numeric or has_seq) and len(weak_entries) < 10:
                weak_entries.append({
                    "entry": pwd,
                    "reason": "Short (<8 chars)" if l < 8 else ("Pure numeric" if is_numeric else "Sequential digits")
                })

        unique_count = len(unique_set)
        dup_rate = round((duplicate_count / total_count) * 100, 2)
        avg_len = round(total_len / total_count, 1)

        # Quality scoring
        quality_score = 100
        if dup_rate > 20:
            quality_score -= 30
        elif dup_rate > 5:
            quality_score -= 15

        numeric_pct = (pure_numeric / total_count) * 100
        if numeric_pct > 30:
            quality_score -= 25

        if avg_len < 8:
            quality_score -= 30

        if quality_score >= 80:
            grade = "A (High Diversity)"
        elif quality_score >= 60:
            grade = "B (Acceptable)"
        elif quality_score >= 40:
            grade = "C (High Redundancy)"
        else:
            grade = "D (Poor / Weak Entries)"

        return {
            "total_entries": total_count,
            "unique_entries": unique_count,
            "duplicate_count": duplicate_count,
            "duplicate_rate_pct": dup_rate,
            "avg_length": avg_len,
            "min_length": min_len if min_len != 99999 else 0,
            "max_length": max_len,
            "pure_numeric_count": pure_numeric,
            "pure_numeric_pct": round(numeric_pct, 1),
            "sequential_count": sequential,
            "sample_weak_entries": weak_entries,
            "quality_grade": grade
        }

    @staticmethod
    def simulate_search_space(
        charset_type: str,
        length: int,
        custom_pool_size: Optional[int] = None,
        attempts_per_sec: float = 1000.0
    ) -> Dict[str, Any]:
        """
        Mathematical simulator of theoretical search space size and exhaustion time.
        """
        length = max(1, min(63, length))
        attempts_per_sec = max(0.1, attempts_per_sec)

        charset_pools = {
            "numeric": (10, "0-9 (10 chars)"),
            "alpha_lower": (26, "a-z (26 chars)"),
            "alpha_mixed": (52, "a-z, A-Z (52 chars)"),
            "alphanumeric": (62, "a-z, A-Z, 0-9 (62 chars)"),
            "ascii_printable": (95, "Full ASCII with Symbols (95 chars)"),
        }

        if custom_pool_size and custom_pool_size > 0:
            pool_size = custom_pool_size
            pool_label = f"Custom Pool ({pool_size} chars)"
        else:
            pool_size, pool_label = charset_pools.get(charset_type, (62, "Alphanumeric (62 chars)"))

        total_space = math.pow(pool_size, length)
        average_keys = total_space / 2.0
        seconds_worst = total_space / attempts_per_sec
        seconds_avg = average_keys / attempts_per_sec

        def format_dur(s: float) -> str:
            if s < 1:
                return "< 1 second"
            elif s < 60:
                return f"{int(s)} seconds"
            elif s < 3600:
                return f"{round(s / 60, 1)} minutes"
            elif s < 86400:
                return f"{round(s / 3600, 1)} hours"
            elif s < 31536000:
                return f"{round(s / 86400, 1)} days"
            elif s < 31536000 * 1000:
                return f"{round(s / 31536000, 1)} years"
            else:
                return f"{s / 31536000:.2e} years (Infeasible)"

        # Educational sample sequence generation
        sample_sequence = []
        if charset_type == "numeric":
            for i in range(min(5, int(total_space))):
                sample_sequence.append(str(i).zfill(length))
        else:
            sample_sequence = ["A" * length, "B" * length, "C" * length]

        return {
            "charset_label": pool_label,
            "pool_size": pool_size,
            "length": length,
            "attempts_per_sec": attempts_per_sec,
            "total_combinations_scientific": f"{total_space:.2e}",
            "total_combinations_exact": f"{int(total_space):,}" if total_space < 1e16 else f"{total_space:.4e}",
            "time_to_exhaust_worst_case": format_dur(seconds_worst),
            "time_to_exhaust_average_50pct": format_dur(seconds_avg),
            "sample_patterns": sample_sequence
        }
