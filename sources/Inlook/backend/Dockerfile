FROM ubuntu:22.04

RUN apt update
RUN apt upgrade -y
RUN apt install -y socat python3-pip

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY server.py server.py
COPY mail.py mail.py
COPY user.py user.py
COPY cipher.py cipher.py

CMD socat -d TCP-LISTEN:1337,reuseaddr,fork EXEC:'python3 server.py'