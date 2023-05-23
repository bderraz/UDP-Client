from bitarray import bitarray
import logging
class CRCErrorDetected(Exception):
    pass


class CRC:

  def __init__(self, poly):
    self.poly = bitarray(poly)
    self.w = len(poly) - 1

  def generateReminder(self, bit_array):
    aumented_message = bit_array + bitarray('0' * self.w)
    register = bitarray(self.w)
    register.setall(0)

    counter = 0
    for bit in aumented_message:
      counter += 1
      register << 1
      register += bitarray(str(bit))

      if register[0]:
        register = register ^ self.poly
      register.pop(0)

    return register

  def generateReminderFromBinary(self, binary_message):
    self.generateReminder(bitarray(binary_message))

  def addCheckSumOnMessage(self, message: str) -> bytes:
    byte_message = message.encode("utf-8")
    bit_message = bitarray()
    bit_message.frombytes(byte_message)
    bit_checksum = self.generateReminder(bit_message)
    byte_reminder = bit_checksum.tobytes()
    logging.info("CHECKSUM:A: " + str(bit_checksum))
    return byte_message + byte_reminder

  def removeCheckSumAndDetectErrors(self, message: bytes) -> str:
    n_pad_bits = bitarray('0' * self.w).padbits
    bit_message = bitarray()
    bit_message.frombytes(message)
    message = bit_message[:len(bit_message) - (self.w + n_pad_bits)]
    check_sum = bit_message[len(bit_message) - self.w - n_pad_bits:]

    receiver_check_sum = self.generateReminder(message)
    logging.info("CHECKSUM:B: " + str(receiver_check_sum))

    if check_sum == receiver_check_sum:
      message_str = message.tobytes().decode("utf-8")
      return message_str
    raise CRCErrorDetected()

