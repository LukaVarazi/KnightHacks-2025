# Use an official Python runtime as a parent image
# Using a slim variant reduces the final image size
FROM python:3.14-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
# This layer is only rebuilt if requirements.txt changes
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size by not storing the cache
# --trusted-host pypi.python.org is good practice if you're behind a firewall
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the application's source code
COPY . .

# Expose the port the app runs on (if it's a web app)
# Change 8000 to whatever port your app uses
EXPOSE 8000

# Define environment variables (optional)
# ENV NAME World

# Run app.py when the container launches
# Using ["python", "app.py"] is the preferred 'exec' form
CMD ["python", "app.py", "--host=0.0.0.0"]
