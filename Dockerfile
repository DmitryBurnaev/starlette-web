FROM python:3.10-slim-buster
WORKDIR /web-project

COPY setup.cfg .
COPY setup.py .

RUN groupadd -r web && useradd -r -g web web
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
		gcc \
		libpq-dev \
		python-dev \
    && pip install .[testing] \
	&& apt-get purge -y --auto-remove gcc python-dev \
	&& apt-get -y autoremove \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

COPY starlette_web ./starlette_web
COPY etc/run_tests.sh .
COPY .coveragerc .
COPY .flake8 .

RUN chown -R web:web /web-project

ENV STARLETTE_SETTINGS_MODULE=starlette_web.core.settings
COPY command.py .
RUN python command.py collectstatic

ENTRYPOINT ["/bin/sh", "/web-project/run_tests.sh"]
