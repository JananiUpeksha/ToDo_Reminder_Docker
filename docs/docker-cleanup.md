# Docker Cleanup Reference

## Remove stopped containers
docker container prune -f

## Remove unused images (keeps tagged ones)
docker image prune -f

## Remove unused images INCLUDING tagged ones not used by any container
docker image prune -af

## Remove unused volumes (WARNING: deletes data in unused volumes)
docker volume prune -f

## Remove everything unused at once (safe - keeps volumes)
docker system prune -f

## Remove EVERYTHING including volumes (destructive - wipes DB data)
docker system prune -af --volumes

## Check disk usage by Docker
docker system df

## Real-time resource usage per container
docker stats

## See all images with sizes
docker images

## See all volumes
docker volume ls
