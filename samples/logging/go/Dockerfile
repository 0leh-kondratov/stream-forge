FROM golang:1.19-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /main .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /main .

# Required for trace correlation
ENV GCP_PROJECT_ID=<MY_GCP_PROJECT_ID>
ENV K_SERVICE=sample-logger-go
ENV APP_ENV=dev

CMD ["/app/main"]
