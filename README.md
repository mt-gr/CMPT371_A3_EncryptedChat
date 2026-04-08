# CMPT371_A3_EncryptedChat

## Murat Guler 301461628 mga170@sfu.ca
## Instructor: Mirza Zaeem Baig
## Semester: Spring 2026

## Demo video
[371 Demo .webm](https://github.com/user-attachments/assets/e7f54b2e-11fc-4331-84b6-aa0883bf93c5)


## Limitations
Simultaneous users:
The following application is designed to only support a 1-on-1 chat, and once a user disconnects the session is over and a new server must be established to continue chatting.
---
TCP Implenentation:
The program uses TCP/IP to garuntee message delivery.
---
End-to-end encryption:
The limitation of simultaenous users comes up in the implementation of the encryption, in order to be most secure keys are only shared between two users.

## Required Libraries
Rsa and pycryptodome

```
pip install rsa
pip install pycryptodome
```

## Step by step usage

Ensure required libraries are installed and you are running at least python 3.10
Download chat.pyw and run the script

As a host:
- Ensure an open port
- Enter nickname
- Enter local IPv4 address
- Enter port
- Press Host Server button

As a client:
- Enter nickname
- Enter host's public IPv4 address
- Enter port
- Press connect to host button

Once connected:
- Enter messages in bottom text box
- Press send button or press enter to send message
- Close GUI once done

