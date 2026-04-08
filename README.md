# CMPT371_A3_EncryptedChat

## Limitations
The following application is designed to only support a 1-on-1 chat, and once a user disconnects the session is over and a new server must be established to continue chatting.

## Required Libraries
Rsa and pycryptodome

```
pip install rsa
pip install pycryptodome
```

## Step by step usage

Ensure required libraries are installed and you are running at least python 3.10

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

