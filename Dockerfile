FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python init_db.py
RUN sed -i "s/app.run(debug=True, port=5000)/app.run(host='0.0.0.0', debug=True, port=5000)/g" app.py
EXPOSE 5000
CMD ["python", "app.py"]
