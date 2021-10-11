import hashlib

description_tags = {
    "meta_start": "{meta_begin}\n",
    "meta_end": "\n{meta_end}\n",
    "body_start": "\n{body_begin}\n",
    "body_end": "\n{body_end}"
}


def create_hash(string):
    return hashlib.md5(string.encode()).hexdigest()


def hash_match(string, hash_in):
    return hash_in == hashlib.md5(string.encode()).hexdigest()
