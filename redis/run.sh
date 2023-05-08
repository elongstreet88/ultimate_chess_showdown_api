# build
docker build . -t redis

# create docker network
docker network create --driver bridge ssot

# check if redis container is running, if not, start it
docker ps | grep redis || docker run -d -p 6379:6379 --network-alias redis --network ssot --name redis -t redis