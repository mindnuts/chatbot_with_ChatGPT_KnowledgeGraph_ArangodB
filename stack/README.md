### basic commands

```
docker compose up -d arangodb

#cd to dump directory
cd ~/Downloads/chatbot_with_ChatGPT_KnowledgeGraph_ArangodB/healthcare_kg_dump
docker run --network stack_arango_net --rm -it --entrypoint /bin/sh -v $PWD:/dump arangodb:3.12


#inside the container
cd /dump
arangorestore \
  --server.endpoint tcp://arangodb:8529 \
  --server.username root \
  --server.password greenapple71 \
  --server.database healthcare \
  --input-directory "/dump" \
  --create-database
```
