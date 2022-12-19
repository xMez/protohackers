from protohackers.m0008_insecure_sockets_layer.obfuscate import Cipher


def test_xor_reversebits_hello():
    spec = bytes.fromhex("02010100")
    cipher = Cipher(spec)
    assert cipher.encrypt(b"hello", 0) == bytes.fromhex("9626b6b676")


def test_addpos_addpos_hello():
    spec = bytes.fromhex("050500")
    cipher = Cipher(spec)
    assert cipher.encrypt(b"hello", 0) == bytes.fromhex("6867707277")


def test_create_cipher():
    spec = bytes.fromhex("027b050100")
    cipher = Cipher(spec)
    assert cipher.encrypt(b"4x dog,5x car\n", 0) == bytes.fromhex(
        "f220ba441884baaad02644a4a87e"
    )
