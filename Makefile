build:
	docker build -t image-message-service .

run:
	docker run --name message-service image-message-service

stop:
	docker stop message-service && docker rm message-service

clean:
	docker rmi image-message-service

.PHONY: build run stop clean