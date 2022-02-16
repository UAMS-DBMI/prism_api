.PHONY: run

last_update: Dockerfile
	docker build -t tcia/prism_api .
	touch $@


run: last_update
	docker run -it \
		-e API_WORKERS=1 \
		-e API_PORT=8080 \
		-e PGHOST=144.30.104.84 \
		-e PGPORT=5433 \
		-e PGUSER=postgres \
		-e PGPASSWORD=example \
		-p 8080:8080 \
		tcia/prism_api

clean:
	rm last_update

push:
	docker push tcia/prism_api:latest