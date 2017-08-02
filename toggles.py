import hashlib


def hashfunc(x):
    return int(hashlib.sha256(x).hexdigest(), 16)

simhash_bytes = 256

shingle_settings = {
    'char': 10,
    'word': 3,
    'shingle_type': 'char'
}

minhash_hash_num = 500
