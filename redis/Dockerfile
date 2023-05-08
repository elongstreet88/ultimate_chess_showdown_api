FROM redis:alpine as runtime

COPY --chown=redis:redis redis.conf redis.conf

USER redis

ENTRYPOINT ["redis-server", "redis.conf"]
