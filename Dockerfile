FROM python:3.12
WORKDIR /root/lebotlent/git

# Copy the source code (located in pwd)
COPY * /root/lebotlent

# Install the application dependencies
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]