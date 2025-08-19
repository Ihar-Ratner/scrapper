1. # Create a backup of your PostgreSQL data
docker run --rm \
  -v scrapper_pg_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz -C /data .

Volume backup:
# Create volume backup
docker run --rm \
  -v scrapper_pg_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_volume_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

SQL Dump Backup:
# Create SQL dump backup
docker exec wb_db pg_dump -U wb_bot -d wb > postgres_dump_$(date +%Y%m%d_%H%M%S).sql
