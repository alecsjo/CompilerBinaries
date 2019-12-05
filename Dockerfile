FROM python:3

ADD CompilerScript.py /

# Install dependencies:
COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["python", "CompilerScript.py"]
