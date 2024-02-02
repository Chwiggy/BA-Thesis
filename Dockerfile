FROM continuumio/anaconda3
WORKDIR /src
COPY environment.yml .
RUN conda env create -f environment.yml
SHELL [ "conda", "run", "-n", "matrix", "bin/bash", "-c" ]

COPY src/main.py .
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "matrix", "python", "main.py"]