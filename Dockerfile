FROM continuumio/anaconda3
WORKDIR /src
COPY osmosis.sh .
RUN osmosis.sh
COPY environment.yml .
RUN conda env create -f environment.yml
SHELL [ "conda", "run", "-n", "matrix", "bin/bash", "-c" ]

COPY src/main.py .
COPY src/utils utils
COPY config.ini .
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "matrix", "python", "main.py", "-c", "config.ini"]