### Lightweight replacement of TCP/IP protocol stack for low bandwidth networks, for example LoRa

Clone repository:
`git clone https://github.com/comradeFreeman/lightweight_stack.git`

Setup Python virtual environment:\
```
cd lightweight_stack
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

Run script, which filename ends with `server`\
Run script, which filename ends with `client`\
Discover and explore TCP+TLS or UDP packets with Wireshark using filters `tcp.srcport == 2000 || tcp.dstport == 2000` or `udp.srcport == 2000 || udp.dstport == 2000` respectively 
