#!/bin/bash

if [ ! -f .env ]; then
    echo -n "JWT_SECRET=" > .env
    echo $RANDOM | md5sum >> .env
fi

docker compose up --build -d