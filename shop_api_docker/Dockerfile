FROM python:3.12

WORKDIR /shop_api

COPY ../pyproject.toml /shop_api
COPY ../lecture_2/__init__.py /shop_api/lecture_2/
COPY ../lecture_2/hw /shop_api/lecture_2/hw

RUN pip install "poetry==1.8.3"
RUN poetry install

CMD ["poetry", "run", "uvicorn", "lecture_2.hw.shop_api.main:app", "--port", "8000", "--host", "0.0.0.0"]
