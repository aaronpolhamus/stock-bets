FROM backend:latest

ENTRYPOINT ["./docker/worker-entrypoint.sh"]
