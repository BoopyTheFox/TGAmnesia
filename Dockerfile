FROM python:3.12-slim

ENV path=/TGAmnesia

VOLUME ${path}
WORKDIR ${path}

COPY app/ ${path}

# Install stuff
RUN apt-get update
RUN apt-get -y install cron
RUN pip install -r requirements.txt

# Set environment variables for cron to launch python successfully
RUN PATH=/usr/local/bin > /var/spool/cron/crontabs/root

# Run stuff
CMD service cron start && python TGAmnesia_bot.py


