import hashlib
def hashfunc(x):
    return int(hashlib.sha256(x).hexdigest(), 16)

simhash_bytes = 256
shingle_size = {'char':5, 'word': 3}
