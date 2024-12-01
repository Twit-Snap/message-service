build:
	docker build -t image-newrelic newrelic/.
	docker build -t image-message-service src/.

run:
	docker run -it --name message-service -p 8082:8082 image-message-service

stop:
	docker stop message-service && docker rm message-service

clean:
	docker rmi image-message-service
	docker rmi image-newrelic

test:
	pytest -v

.PHONY: build run stop clean test 
