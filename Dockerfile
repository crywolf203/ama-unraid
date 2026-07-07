FROM lsiobase/ubuntu:focal
LABEL maintainer="RandomNinjaAtk"

ENV TITLE="Automated Music Archiver (AMA)"
ENV TITLESHORT="AMA"
ENV VERSION="2.5.1"
ENV XDG_CONFIG_HOME="/config/deemix/xdg"
RUN \
	echo "************ install dependencies ************" && \
	echo "************ install and upgrade packages ************" && \
	apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y --no-install-recommends \
		netbase \
		jq \
		flac \
		eyed3 \
		python3 \
		ffmpeg \
		opus-tools \
		python3-pip \
		wget \
		xz-utils \
		ca-certificates && \
	rm -rf \
		/tmp/* \
		/var/lib/apt/lists/* \
		/var/tmp/* && \
	echo "************ install python packages ************" && \
python3 -m pip install --no-cache-dir \
  certifi==2021.10.8 \
  charset-normalizer==2.0.12 \
  idna==3.3 \
  requests==2.27.1 \
  urllib3==1.26.9 \
  pycryptodomex==3.14.1 \
  mutagen==1.45.1 \
  yq==2.14.0 \
  deezer-py==1.3.7 \
  deemix==3.6.6 && \
	echo "************ install rsgain ************" && \
	mkdir -p /tmp/rsgain /usr/local/bin && \
	wget -O /tmp/rsgain/rsgain.tar.xz https://github.com/complexlogic/rsgain/releases/download/v3.7/rsgain-3.7-Linux.tar.xz && \
	tar -xJf /tmp/rsgain/rsgain.tar.xz -C /tmp/rsgain && \
	find /tmp/rsgain -type f -name rsgain -exec cp {} /usr/local/bin/rsgain \; && \
	chmod +x /usr/local/bin/rsgain && \
	rsgain --version && \
	rm -rf /tmp/rsgain && \
	echo "************ setup dl client config directory ************" && \
	echo "************ make directory ************" && \
	mkdir -p "${XDG_CONFIG_HOME}/deemix"
 
# copy local files
COPY root/ /
 
# set work directory
WORKDIR /config
