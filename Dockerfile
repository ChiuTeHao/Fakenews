FROM node:10-alpine

# Install chromium73 which is the latest available in alpine.
RUN apk update && apk upgrade && \
    echo @edge http://nl.alpinelinux.org/alpine/edge/community >> /etc/apk/repositories && \
    echo @edge http://nl.alpinelinux.org/alpine/edge/main >> /etc/apk/repositories && \
    apk add --no-cache \
      chromium@edge=~73.0.3683.103 \
      nss@edge \
      freetype@edge \
      freetype-dev@edge \
      harfbuzz@edge \
      ttf-freefont@edge

# Don't install the chromium bundled with puppeteer.
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD true

# Puppeteer v1.12.2 works with Chromium 73.
RUN yarn add puppeteer@1.12.2 express body-parser

# Add user so we don't need --no-sandbox.
RUN addgroup -S pup && adduser -S -g pup pup \
    && mkdir -p /home/pup/Downloads /app /home/pup/img \
    && chown -R pup:pup /home/pup \
    && chown -R pup:pup /app

# Run everything after as non-privileged user.
USER pup
WORKDIR /home/pup
COPY server.js .

EXPOSE 6175
CMD ["node", "server.js"]
