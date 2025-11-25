FROM public.ecr.aws/lambda/python:3.12

# Update system packages including libcap
RUN dnf update -y libcap && dnf clean all

# Upgrade pip to version 25.3
RUN pip3 install --upgrade pip==25.3

COPY ./api ./api

COPY requirements.txt .

RUN pip3 install -r requirements.txt -U --no-cache-dir

CMD [ "api.app.handler" ]