"""Obfuscation module implementing a cipher sequence."""
import logging
import random
from functools import partial
from typing import Callable, Generator

BYTE_SIZE = 256

logging.basicConfig(level=logging.DEBUG)


class CipherError(Exception):
    """Error constructing cipher sequence."""


class Cipher:
    """Cipher class for the current cipher."""

    def __init__(self, spec: bytes) -> None:
        """Initialize a cipher."""
        try:
            logging.info("Got cipher spec: %s", spec.hex())
            self.cipher_sequence = list(self.get_cipher_sequence(spec))
            self.validate_cipher()
        except ValueError as error:
            logging.error("Failed to initialize cipher, invalid value: %s", error)
            raise CipherError from error
        except CipherError as error:
            logging.error("Invalid cipher: %s", error)
            raise error
        logging.info("Initialized cipher: %s", spec.hex())

    @staticmethod
    def reversebits(line: bytearray, **_) -> bytearray:
        """Reverse the order of bits in the byte.

        Parameters
        ----------
        line : bytearray
            Line to bit reverse

        Returns
        -------
        bytearray
            Bit reversed line
        """
        for i, byte in enumerate(line):
            line[i] = int(f"{byte:08b}"[::-1], 2)
        return line

    @staticmethod
    def xor(line: bytearray, value: int = 0, **_) -> bytearray:
        """XOR each byte in a bytearray.

        Parameters
        ----------
        line : bytearray
            Array to XOR
        value : int, optional
            value to XOR by, by default 0

        Returns
        -------
        bytearray
            XOR'd array
        """
        for i, byte in enumerate(line):
            byte ^= value
            byte %= BYTE_SIZE
            line[i] = byte
        return line

    @staticmethod
    def xorpos(line: bytearray, pos: int = 0, **_) -> bytearray:
        """XOR each byte in a bytearray by it's position in the stream.

        Parameters
        ----------
        line : bytearray
            Array to XOR
        pos : int, optional
            Current position of the stream, by default 0

        Returns
        -------
        bytearray
            XOR'd array
        """
        for i, byte in enumerate(line):
            value = pos + i
            byte ^= value
            byte %= BYTE_SIZE
            line[i] = byte
        return line

    @staticmethod
    def add(line: bytearray, value: int = 0, sub: bool = False, **_) -> bytearray:
        """ADD `value` to each byte in a bytearray, modulo BYTE_SIZE.

        Parameters
        ----------
        line : bytearray
            Array to ADD
        value : int, optional
            value to ADD, by default 0
        sub : bool, optional
            Change to SUB for deciphering, by default False

        Returns
        -------
        bytearray
            ADD'd array
        """
        for i, byte in enumerate(line):
            if sub:
                byte -= value
            else:
                byte += value
            byte %= BYTE_SIZE
            line[i] = byte
        return line

    @staticmethod
    def addpos(line: bytearray, pos: int = 0, sub: bool = False, **_) -> bytearray:
        """ADD the position in the stream to each byte in a bytearray, modulo BYTE_SIZE.

        Parameters
        ----------
        line : bytearray
            Array to ADD
        pos : int, optional
            Current position of the stream, by default 0
        sub : bool, optional
            Change to SUB to deciphering, by default False

        Returns
        -------
        bytearray
            _description_
        """
        for i, byte in enumerate(line):
            if sub:
                byte -= pos + i
            else:
                byte += pos + i
            byte %= BYTE_SIZE
            line[i] = byte
        return line

    def get_cipher_sequence(self, spec: bytes) -> Generator[Callable, None, None]:
        """Create a cipher sequence from a bytes specification array.

        Parameters
        ----------
        spec : bytes
            Cipher specification as a bytes array

        Yields
        ------
        Generator[Callable, None, None]
            Cipher sequence

        Raises
        ------
        ValueError
            Invalid cipher specification
        """
        iterator = iter(spec)
        while byte := next(iterator):
            match byte:
                case 0:
                    return
                case 1:
                    yield self.reversebits
                case 2:
                    value = next(iterator)
                    yield partial(self.xor, value=value)
                case 3:
                    yield self.xorpos
                case 4:
                    value = next(iterator)
                    yield partial(self.add, value=value)
                case 5:
                    yield self.addpos
                case _:
                    raise ValueError

    def validate_cipher(self):
        """Validate that the cipher is functional and not a no-op cipher."""
        random_message = bytes(random.getrandbits(8) for _ in range(BYTE_SIZE))
        encrypted = self.encrypt(random_message, 0)
        decrypted = self.decrypt(encrypted, 0)
        if random_message != decrypted:
            raise CipherError("Broken cipher")
        if random_message == encrypted:
            raise CipherError("No-op cipher")

    def encrypt(self, line: bytes, pos: int) -> bytes:
        """Encrypt a line using the cipher.

        Parameters
        ----------
        line : bytes
            Input to be encrypted

        pos : int
            Position in the stream

        Returns
        -------
        bytes
            Encrypted output
        """
        result = bytearray(line)
        for cipher in self.cipher_sequence:
            result = cipher(result, pos=pos)
        return result

    def decrypt(self, line: bytes, pos: int) -> bytes:
        """Decrypt a line using the cipher.

        Parameters
        ----------
        line : bytes
            Input to be decrypted

        pos : int
            Position in the stream

        Returns
        -------
        bytes
            Decrypted output
        """
        result = bytearray(line)
        for cipher in self.cipher_sequence[::-1]:
            result = cipher(result, pos=pos, sub=True)
        return result
