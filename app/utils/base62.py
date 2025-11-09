import hashlib

BASE62_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def encode_base62(num: int) -> str:
    """Convert integer to base62 string"""
    if num == 0:
        return BASE62_CHARS[0]

    result = []
    while num > 0:
        result.append(BASE62_CHARS[num % 62])
        num //= 62

    return ''.join(reversed(result))

def generate_short_code(url: str, xid: int, length: int = 10) -> str:
    """Generate short code using combination of ID and hash"""
    # Use ID as primary source for uniqueness
    hash_input = f"{xid}{url}".encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()

    # Convert first 16 hex characters to integer
    hash_num = int(hash_digest[:16], 16)

    # Encode the hash as base62
    encoded = encode_base62(hash_num)

    # If shorter than desired length, pad with encoded ID
    while len(encoded) < length:
        id_encoded = encode_base62(xid)
        encoded = encoded + id_encoded

    # Truncate to exact length
    return encoded[:length]
