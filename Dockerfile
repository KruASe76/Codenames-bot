FROM python:3.11
RUN pip install pipenv
WORKDIR /bot
COPY . .
RUN yes | pipenv install
CMD pipenv run python3 main.py
