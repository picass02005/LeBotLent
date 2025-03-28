# SPDX-License-Identifier: MIT
# Copyright (C) 2024 picasso2005 <clementduran0@gmail.com> - All Rights Reserved

FROM python:3.12
WORKDIR /root/lebotlent

# Copy the source code
# /!\ pwd must be where the code is
# COPY <src> <dest>
COPY . .

# Install the application dependencies
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]