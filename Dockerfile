FROM python:3.6

ARG BUILD_DATE
ARG VCS_REF

ARG ROCKSDB_REPO='https://github.com/facebook/rocksdb.git'
ARG ROCKSDB_VERSION='5.2.1'
ARG ROCKSDB_TAG="rocksdb-${ROCKSDB_VERSION}"

ARG MCCORTEX_VERSION='geno_kmer_count'

## Install dependencies
RUN set -x && echo 'deb http://deb.debian.org/debian experimental main' > /etc/apt/sources.list.d/experimental.list
RUN apt-get update -y
RUN apt-get install -y curl git liblzma-dev libbz2-dev zlib1g-dev libgflags-dev libjemalloc-dev libsnappy-dev libtbb-dev libzstd-dev  wget build-essential liblz4-dev python3 python3-pip
RUN pip3 install --upgrade pip

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

## Install rocksdb
#RUN git clone $ROCKSDB_REPO
#WORKDIR /usr/src/app/rocksdb
#RUN git checkout tags/${ROCKSDB_TAG}
#RUN make -j$(nproc) shared_lib
#RUN make install-shared
#RUN strip /usr/local/lib/librocksdb.so.${ROCKSDB_VERSION}

ENV CPLUS_INCLUDE_PATH=${CPLUS_INCLUDE_PATH}:`pwd`/include
ENV CPLUS_INCLUDE_PATH=${CPLUS_INCLUDE_PATH}:/usr/src/app/rocksdb/include
ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:`pwd`:/usr/src/app/rocksdb/
ENV LIBRARY_PATH=${LIBRARY_PATH}:`pwd`:/usr/src/app/rocksdb/
WORKDIR /usr/src/app/

## Install berkeleydb
ENV BERKELEY_VERSION 4.8.30
# Download, configure and install BerkeleyDB
RUN wget -P /tmp http://download.oracle.com/berkeley-db/db-"${BERKELEY_VERSION}".tar.gz && \
    tar -xf /tmp/db-"${BERKELEY_VERSION}".tar.gz -C /tmp && \
    rm -f /tmp/db-"${BERKELEY_VERSION}".tar.gz
RUN cd /tmp/db-"${BERKELEY_VERSION}"/build_unix && \
    ../dist/configure && make && make install

## Install Mykrobe for variant search
RUN git clone --branch feature/background-db-path https://github.com/Mykrobe-tools/mykrobe.git mykrobe-predictor
WORKDIR /usr/src/app/mykrobe-predictor
RUN git clone --recursive -b ${MCCORTEX_VERSION} https://github.com/Mykrobe-tools/mccortex && cd mccortex && make
WORKDIR /usr/src/app/mykrobe-predictor
RUN pip3 install -r requirements.txt && python3 setup.py install
RUN mykrobe panels update_metadata && mykrobe panels update_species all
WORKDIR /usr/src/app/


## Install bigsi
COPY . /usr/src/app
RUN pip3 install cython
RUN pip3 install -r requirements.txt
RUN pip3 install bsddb3==6.2.5
RUN pip3 install uWSGI==2.0.18

# install bigsi
WORKDIR /usr/src/app
RUN python3 setup.py install

CMD bigsi --help