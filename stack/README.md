### basic commands

```
docker compose up -d arangodb

#cd to dump directory
docker run --network stack_arango_net --rm -it --entrypoint /bin/sh -v $PWD:/dump arangodb:3.12

#inside the container

arangorestore \
  --server.endpoint tcp://arangodb:8529 \
  --server.username root \
  --server.password greenapple71 \
  --server.database healthcare \
  --input-directory "dump"

```