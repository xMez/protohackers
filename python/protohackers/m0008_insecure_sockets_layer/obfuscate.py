"""Obfuscation module implementing a cipher sequence."""


import logging
import random
from functools import partial
from typing import Callable, Generator, Optional


class Cipher:
    """Cipher class for the current cipher."""

    def __init__(self, spec: bytes) -> None:
        """Initialize a cipher."""
        self.log = logging.Logger(__name__, logging.INFO)
        try:
            self.cipher_sequence = list(self.get_cipher_sequence(spec))
            self.validate_cipher()
        except ValueError as error:
            self.log.error("Failed to initialize cipher, invalid value: %s", error)
            raise Exception from error
        except AssertionError as error:
            self.log.error("Invalid cipher: No-op")
            raise Exception from error

    @staticmethod
    def reversebits(line: bytearray) -> bytearray:
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
        result = bytearray(line)
        for i, byte in enumerate(result):
            result[i] = int(f"{byte:08b}"[::-1], 2)
        return result

    @staticmethod
    def xor(line: bytearray, value: int = 0) -> bytearray:
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
        result = bytearray(line)
        for i, _ in enumerate(result):
            result[i] ^= value
        return result

    @staticmethod
    def xorpos(line: bytearray, pos: int = 0) -> bytearray:
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
        result = bytearray(line)
        for i, _ in enumerate(result):
            result[i] ^= pos + i
        return result

    @staticmethod
    def add(line: bytearray, value: int = 0, sub: Optional[bool] = None) -> bytearray:
        """ADD `value` to each byte in a bytearray, modulo 256.

        Parameters
        ----------
        line : bytearray
            Array to ADD
        value : int, optional
            value to ADD, by default 0
        sub : bool, optional
            Change to SUB for deciphering, by default None

        Returns
        -------
        bytearray
            ADD'd array
        """
        if sub:
            value = -value
        result = bytearray(line)
        for i, byte in enumerate(result):
            byte += value
            byte %= 256
            result[i] = byte
        return result

    @staticmethod
    def addpos(line: bytearray, pos: int = 0, sub: Optional[bool] = None) -> bytearray:
        """ADD the position in the stream to each byte in a bytearray, modulo 256.

        Parameters
        ----------
        line : bytearray
            Array to ADD
        pos : int, optional
            Current position of the stream, by default 0
        sub : bool, optional
            Change to SUB to deciphering, by default None

        Returns
        -------
        bytearray
            _description_
        """
        result = bytearray(line)
        for i, byte in enumerate(result):
            if sub:
                byte -= pos + i
            else:
                byte += pos + i
            byte %= 256
            result[i] = byte
        return result

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
        """Validate that the cipher is not a no-op cipher."""
        test_string = b"The quick brown fox jumps over the lazy dog\n"
        pos = random.randint(0, 255)  # nosec
        assert test_string == self.decrypt(self.encrypt(test_string, pos), pos)  # nosec

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
            match cipher:
                case self.xorpos | self.addpos:
                    result = cipher(result, pos)
                case _:
                    result = cipher(result)
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
            match cipher:
                case self.xorpos:
                    result = cipher(result, pos)
                case self.add:
                    result = cipher(result, sub=True)
                case self.addpos:
                    result = cipher(result, pos, sub=True)
                case _:
                    result = cipher(result)
        return result
