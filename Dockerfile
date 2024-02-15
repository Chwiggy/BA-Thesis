FROM debian
WORKDIR /src

#Installing osmosis
RUN apt-get update
RUN apt-get -y install osmosis --fix-missing

# setting up python environment
RUN apt-get -y install python3-pip
RUN apt-get -y install python3.11-venv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

#Installing python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/main.py .
COPY src/utils utils
COPY src/data/indices/geofabrik_downloadindex.json .

RUN mkdir osm_data

ENTRYPOINT ["python", "main.py"]