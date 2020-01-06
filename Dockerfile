FROM python:3

ADD CompilerScript.py /

# Install dependencies:
COPY requirements.txt .
RUN pip install -r requirements.txt
# RUN git clone --recursive https://github.com/ethereum/solidity.git

CMD ["python", "CompilerScript.py"]
