FROM python:3.9

LABEL maintainer="vanek"
LABEL t="backend"

WORKDIR /app/backend
COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
