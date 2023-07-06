FROM alpine:latest
WORKDIR /bot
COPY . /bot
RUN apk update && apk upgrade
RUN apk add --no-cache ffmpeg
RUN apk add --no-cache opus-dev
ENV PYTHONBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN pip3 install --no-cache-dir -r requirements.txt
CMD ["python3","newpythonbot.py"]