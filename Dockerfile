FROM node:24-alpine AS deemix-builder

ARG DEEMIX_REPO=https://github.com/crywolf203/deemix.git
# renovate: datasource=git-refs packageName=https://github.com/crywolf203/deemix currentValue=fix-docker-temp-artwork-permissions
ARG DEEMIX_REF=4d5159657abac89074e96bb48c7a15005502745b

RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++

RUN corepack enable

WORKDIR /src

RUN git clone --filter=blob:none "$DEEMIX_REPO" . \
    && git checkout "$DEEMIX_REF"

RUN pnpm install --frozen-lockfile

RUN pnpm turbo build --filter=deemix-cli...

RUN cd /src/packages/cli \
    && /src/node_modules/.bin/pkg \
       . \
       --targets node20-linux-x64 \
       --output /tmp/deemix

RUN chmod 0755 /tmp/deemix \
    && test -x /tmp/deemix \
    && ls -lh /tmp/deemix

FROM lsiobase/ubuntu:focal
LABEL maintainer="RandomNinjaAtk"

ENV TITLE="Automated Music Archiver (AMA)"
ENV TITLESHORT="AMA"
ENV VERSION="2.6.0"
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
  yq==2.14.0 && \
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
 
# Bambanah Deemix standalone CLI
COPY --from=deemix-builder /tmp/deemix /usr/local/bin/deemix
RUN chmod 0755 /usr/local/bin/deemix

# copy local files
COPY root/ /
 
# set work directory
WORKDIR /config
