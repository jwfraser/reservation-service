# Requirements

* docker
* docker-compose

# Running services

Start docker-compose

```bash
docker-compose up --build
```

Endpoint is available once api_service shows `Application startup complete.` 

# Notes

* Docker-compose has `DEBUG=1` for localstack to see raw email output of SES

# Endpoint

http://localhost:8080/

Swagger Docs can be found at http://localhost:8080/docs/
ReDocs can be found at at http://localhost:8080/redoc

# Example Request

```bash
curl -X POST "http://localhost:8080/reservations/" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{\"start_time\":\"2021-02-22T01:10:52.559Z\",\"end_time\":\"2021-02-22T01:13:52.559Z\",\"employee_email\":\"user@example.com\",\"employee_name\":\"string\",\"workplace\":\"string\"}"
```

# Uses

* FastAPI
* Pydantic
* SQLAlchemy
* Postgres
* uvicorn
* localstack-full