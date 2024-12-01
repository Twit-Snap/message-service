build:
    docker build -t image-message-service .

run:
    docker run --name message-service -p 8082:8082 image-message-service

stop:
    docker stop message-service && docker rm message-service

clean:
    docker rmi image-message-service

test:
    pytest -v

.PHONY: build run stop clean test 