import socket as s
import time
import threading
import logging
import CRC
import random

logging.basicConfig(level=logging.INFO)

UDP_IP = "143.47.184.219"
UDP_PORT = 5382

response_received = threading.Event()
akn_received = threading.Event()
akn_received.set()
message_acknowledged_ctl = {}
response_buffer = ""
response_lock = threading.Lock()
sequence_number = random.randint(0, 99999)
already_received_sequence_numbers = []
crc = CRC.CRC('100000100110000010001110110110111') #CRC32 - Ethernet Poly

def send_acknowledgement_to_sender(sock, user, akn):
    protocol = ("SEND " + user + " ").encode("utf-8")
    message_with_akn = encode_acknowledged_number(akn)
    end_line = '\n'.encode("utf-8")
    send_message(sock,
                 protocol + crc.addCheckSumOnMessage(message_with_akn) + end_line,
                 wait_for_acknowledment=False,
                 in_bytes=True)
def encode_acknowledged_number(akn):    
    return "*" + str(akn)

def decode_acknowledged_number(message):
    return int(message[1:])

def encode_sequence_number(string):
    global sequence_number
    sequence_number = (sequence_number + 1) % 100000
    return f'{sequence_number:05d}' + string

def decode_sequence_number(string):
    return string[5:], int(string[:5])

"""
Function to send an entire message to the supplied socket.
Breaks the message into multiple packets if it cannot be sent in one piece.
"""

def send_message_helper(sock, message:bytes):
    logging.info("SEND: " + message.decode("utf-8", errors='ignore'))
    bytes_len = len(message)
    num_bytes_to_send = bytes_len
    while num_bytes_to_send > 0:
        num_bytes_to_send -= sock.sendto(message[bytes_len - num_bytes_to_send:], (UDP_IP, UDP_PORT))

def send_message(sock, message, wait_for_acknowledment = False, in_bytes = False):
    message_in_bytes = message
    if not in_bytes:
        message_in_bytes = message.encode("utf-8")

    response_received.clear()

    if wait_for_acknowledment:
        akn_received.wait()
        message_acknowledged_ctl[sequence_number] = "SENT"
        number_of_trys = 1
        while message_acknowledged_ctl[sequence_number] != "AKN":
            if number_of_trys >= 5:
                logging.info("Max retry exceeded... Canceling send...")
                break
            if number_of_trys > 1:
                logging.info("Message timeout... Retrying...")
            send_message_helper(sock, message_in_bytes)
            akn_received.clear()
            number_of_trys += 1
            if response_received.wait(3):
                with response_lock:
                    if response_buffer.startswith("BAD-DEST-USER"):
                        print("Recipient with username " + recipient + " could not be found. Please try again.")
                        break
                    elif response_buffer.startswith("BAD-RQST-BODY"):
                        print("Invalid message body. Please try again.")
                        break
            # time.sleep(3)
        akn_received.set()
    else:
        send_message_helper(sock, message_in_bytes)


"""
Constantly listenes to incoming messages.
If a DELIVERY is received, print to the terminal.
Otherwise pass the response to the main thread via a global variable.
"""
def message_listener(sock):
    global response_buffer
    global sequence_number
    while True:
        try:
            resp = b''
            while True:
                data, addr = sock.recvfrom(1024)
                resp += data
                if resp[-1] == 10:
                    break
            logging.info("RECEIVED: "+ resp.decode("utf-8", errors='ignore'))

            if resp.startswith("DELIVERY".encode("utf-8")):
                sender = resp.decode("utf-8", errors='ignore').split(" ")[1]
                raw_message = resp[10+len(sender):]
                raw_message = raw_message[:-1]
                raw_message = crc.removeCheckSumAndDetectErrors(raw_message)

                # message is an AKN
                if raw_message[0] == '*':
                    message_acknowledged_ctl[int(raw_message[1:])] = "AKN"
                    print("Message sent successfully")
                else:
                    received_message, sn = decode_sequence_number(raw_message)
                    # sequence_number = sn
                    send_acknowledgement_to_sender(sock, sender, sn)

                    if sn not in already_received_sequence_numbers:
                        already_received_sequence_numbers.append(sn)
                        print("Message from " + sender + ": " + received_message)
            elif resp.startswith("SEND-OK".encode("utf-8")):
                    #we ignore the "SEND OK" since we are using our own ack implementation
                    pass
            else:
                resp = resp.decode("utf-8", errors="ignore")
                with response_lock:
                    response_buffer = resp
                    response_received.set()
        except CRC.CRCErrorDetected:
            logging.error("CRC error detected")
        except OSError as e:
            return


if __name__ == "__main__":    
    print('Welcome to the chat client!\nPlease log in by supplying your username.')
    sock = s.socket(s.AF_INET, s.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 0))
    
    listener = threading.Thread(target=message_listener, args=(sock,))
    listener.start()

    while True:
        response_received.clear()
        try:
            username = input("Username: ")
        except KeyboardInterrupt:
            sock.close()
            quit()

        send_message(sock, "HELLO-FROM " + username + "\n")

        response_received.wait()
        with response_lock:
            if response_buffer.startswith("HELLO"):
                print("Connected successfully")
                break
            elif response_buffer.startswith("IN-USE"): 
                print("This username is already taken. Please try a different name.")
                continue
            elif response_buffer.startswith("BAD-RQST-BODY"):
                print("Invalid username. Please use a different name.")
                continue
            elif response_buffer.startswith("BUSY"):
                print("Maximum number of clients reached. ", end="")
                continue
    response_received.clear()

    print('''
To view a list of all currently logged-in users, type "!who".
To send a message to another user, type "@username message".
To shutdown the client, type "!quit".
To send a configuration command, type "!config".
''')  
    
    listener = threading.Thread(target=message_listener, args=(sock,))
    listener.start()

    while True:
        try:
            command = input("")
        except KeyboardInterrupt:
            sock.close()
            break

        if command == "!quit":
            sock.close()
            break
        
        elif command == "!who":
            send_message(sock, "LIST\n")
            response_received.wait()
            with response_lock:
                if response_buffer.startswith("LIST-OK"):
                        print("Users that are currently logged in: ")
                        print(response_buffer[8:].replace(",", ", "))
            response_received.clear()

        elif command == "!config":
            config_command = input("Input the configure message: ")
            config_command += '\n'
            send_message(sock, config_command)
            response_received.wait()
            with response_lock:
                print(response_buffer)
            response_received.clear()

        elif command.startswith("@"):
            recipient = command.split(" ")[0][1:]
            # +2 to ignore the '@' and space
            message = command[len(recipient)+2:]
            protocol = ("SEND " + recipient + " ").encode("utf-8")
            message_with_akn = encode_sequence_number(message)
            end_line = '\n'.encode("utf-8")
            send_message(sock,
                         protocol + crc.addCheckSumOnMessage(message_with_akn) + end_line,
                         wait_for_acknowledment=True,
                         in_bytes=True)


    listener.join()
    print("Connection closed.")
