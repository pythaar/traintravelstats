FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/pythaar/traintravelstats.git .

RUN pip3 install -r requirements.txt

EXPOSE 27053

HEALTHCHECK CMD curl --fail http://localhost:27053/_stcore/health

ENTRYPOINT ["shiny", "run", "src/app.py", "--port=27053"]