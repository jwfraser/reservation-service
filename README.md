# Requirements

docker/docker-compose

# Using

Start docker-compose

```bash
docker-compose up --build
```

Endpoint is available at http://localhost:8080/ once api_service shows `Application startup complete.` 

# Example Query

```bash
curl -X POST "http://localhost:8080/" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{\"start_time\":\"2021-02-22T00:13:45.464Z\",\"end_time\":\"2021-02-22T01:13:45.464Z\",\"employee_email\":\"user@example.com\",\"employee_name\":\"string\",\"workplace\":\"string\"}"
```