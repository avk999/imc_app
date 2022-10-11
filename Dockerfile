

FROM python:3

EXPOSE 5999
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ADD requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /
ADD . /
RUN markdown2 /README.md > /static/readme.html 
CMD ["gunicorn", "--bind", "0.0.0.0:5999", "-w", "2","--timeout", "300", "webapp:app"]



