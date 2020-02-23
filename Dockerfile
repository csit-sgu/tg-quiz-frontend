FROM python:3.7-alpine

WORKDIR /app
COPY . .

RUN apk add --update --no-cache --virtual .build-deps \
         openssl-dev \
         g++ \
         libffi-dev && \
    apk add --update --no-cache \
        tzdata \
        git && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps && \
    rm -rf /var/cache/apk/*

CMD [ "python3", "bot.py" ]