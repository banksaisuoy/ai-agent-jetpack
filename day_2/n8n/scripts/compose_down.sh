echo "กำลังหยุด container, network และ resource อื่น ๆ ที่ถูกสร้างโดย Docker Compose..."
docker compose down
# docker compose down -v
# หยุดและลบ container, network และ resource อื่น ๆ ที่ถูกสร้างโดย Docker Compose
# บรรทัดที่ถูกคอมเมนต์ไว้ (# docker compose down -v) จะลบ volumes ด้วย หากนำ # ออกa
# คำสั่ง รัน ./scripts/compose_up.sh  ในคลิกขวา กด open in unt