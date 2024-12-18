FROM python:3.12
WORKDIR /usr/local/LeBotLent

# Copy the source code (located in pwd)
COPY * ./

# Install the application dependencies
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]