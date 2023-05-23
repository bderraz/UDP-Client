# UDP Chat Client
The UDP Chat Client is a Python-based client application that facilitates communication between users over an unreliable network using UDP (User Datagram Protocol) sockets. The goal of the project is to provide a chat functionality while ensuring reliable message delivery despite the inherent unreliability of UDP.

# How it Works
To ensure reliable message delivery over an unreliable network, the UDP Chat Client implements the following methods:

1. **Acknowledgment Mechanism**: The client sends messages to the server and waits for an acknowledgment (ACK) from the server. If an ACK is not received within a specified timeout period, the client retransmits the message. This ensures that messages are successfully delivered even if some packets are lost.

2. **Sequence Numbering**: Each message is assigned a unique sequence number. The recipient sends an acknowledgement (AKN) containing the sequence number to confirm the successful receipt of the message. If an AKN is not received, the sender retransmits the message. This ensures that messages are not duplicated or lost during transmission.

3. **Checksum Validation**: The client uses CRC to add a checksum to the message. The server verifies the checksum upon receipt and detects any errors in the message. If a message is corrupted, the server requests retransmission from the client.

4. **Message Buffering**: The client maintains a buffer to store received messages until they are successfully delivered or acknowledged. This allows the client to handle out-of-order message delivery and retransmit any lost or unacknowledged messages.

5. **Timeout and Retransmission**: The client sets a timeout period for receiving acknowledgments (ACKs) from the server. If the ACK for a sent message is not received within the timeout period, the client retransmits the message. This mechanism helps compensate for packet loss or network delays and ensures that messages reach their intended recipients.

6. **Selective Repeat**: The client employs the Selective Repeat protocol to handle out-of-order message delivery. When a message is sent, it includes a sequence number, allowing the recipient to identify the correct order of messages. If a message is received out of order, the client buffers it until the missing messages are received and can be properly sequenced.

7. **Flow Control**: The client implements flow control mechanisms to regulate the rate of message transmission based on the capacity and availability of the network. It ensures that the sender does not overwhelm the recipient or the network with a flood of messages, avoiding congestion and improving overall message delivery efficiency.

8. **Error Detection and Correction**: The client utilizes CRC (Cyclic Redundancy Check) to detect and correct errors in the received messages. By calculating and comparing checksums, the client can identify corrupted or altered messages. If an error is detected, the client requests retransmission of the affected message from the server.

9. **Message Fragmentation and Reassembly**: To accommodate message sizes that exceed the maximum payload of UDP packets, the client breaks large messages into smaller fragments for transmission. The recipient reassembles the fragments to reconstruct the complete message. This approach ensures that messages of any size can be reliably transmitted over the network.
