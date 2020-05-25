FROM backend:latest

ENTRYPOINT ["./docker/beat_worker-entrypoint.sh"]
