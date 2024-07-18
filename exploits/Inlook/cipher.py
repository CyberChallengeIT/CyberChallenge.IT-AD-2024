from Crypto.Util.number import getPrime
from Crypto.Util.Padding import pad, unpad
from hashlib import sha256
from math import gcd
import random

N_BITS = 256

def gen_primes(n_bits=N_BITS):
    p = getPrime(n_bits)
    q = getPrime(n_bits)

    return p, q

def L(x, p):
    return (x-1)//p

def gen_key(n_bits=N_BITS):
    p, q = gen_primes(n_bits)
    n = p**2*q
    g = 2
    h = pow(g, n, n)
    return (p, q), (n, g, h)

def encrypt(pt: bytes, pk: tuple, n_bits=N_BITS):
    pt = pad(pt, n_bits//8)
    n, g, h = pk
    blocks = [pt[i:i + n_bits//8] for i in range(0, len(pt), n_bits//8)]
    ct = b""
    for b in blocks:
        m = int.from_bytes(b, "big")
        r = random.randint(0, n-1)
        c = (pow(g, m, n)*pow(h, r, n)) % n
        ct += c.to_bytes((n_bits*3)//8, "big")
    
    return ct

def decrypt(ct: bytes, sk: tuple, n_bits=N_BITS):
    p, q = sk
    g = 2
    g_p = pow(g, p-1, p**2)
    inv_g_p = pow(L(g_p, p), -1, p)
    blocks = [ct[i:i + (n_bits*3)//8] for i in range(0, len(ct), (n_bits*3)//8)]
    pt = b""
    for b in blocks:
        c = int.from_bytes(b, "big")
        c_p = pow(c, p-1, p**2)
        m = (L(c_p, p)*inv_g_p) % p
        pt += m.to_bytes(n_bits//8, "big")

    pt = unpad(pt, n_bits//8)
    return pt

def sign(sk: tuple, msg: bytes):
    p, q = sk
    n = p**2*q

    g = pow(2, p*(q-1), n)
    x = random.randint(0, p-1)
    y = pow(g, x, n)
    hm = int.from_bytes(sha256(msg).digest(), 'big')
    
    k = 2
    while gcd(k, p-1) != 1:
        k = random.randint(0, p-1)
    k_inv = pow(k, -1, p-1)

    r = pow(g, k, n)
    s = ((hm - x*r)*k_inv) % (p-1)
    
    return (r, s), (n, g, y)

def verify(sig: tuple, pk: tuple, msg: bytes):
    n, g, y = pk
    r, s = sig
    hm = int.from_bytes(sha256(msg).digest(), 'big')
    return pow(g, hm, n) == (pow(r, s, n)*pow(y, r, n))%n

