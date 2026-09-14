FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e packages/project-finance -r apps/api/requirements.txt
EXPOSE 8000
