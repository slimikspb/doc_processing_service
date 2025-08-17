#!/bin/bash

echo "🚀 Запуск надежной версии Document Processing Service"
echo "=================================================="

# 1. Остановить и удалить старые контейнеры
echo "1. Останавливаем старые контейнеры..."
docker-compose down --remove-orphans || true
docker-compose -f docker-compose.yml down --remove-orphans || true

# 2. Удалить старые образы
echo "2. Удаляем старые образы..."
docker rmi $(docker images | grep doc_processing_service | awk '{print $3}') 2>/dev/null || true
docker rmi $(docker images | grep doc-processing-service | awk '{print $3}') 2>/dev/null || true

# 3. Очистить Docker кэш
echo "3. Очищаем Docker кэш..."
docker builder prune -af
docker system prune -af

# 4. Собрать новую версию с надежными зависимостями
echo "4. Собираем новую reliable версию..."
docker-compose -f docker-compose.reliable.yml build --no-cache --pull

# 5. Запустить новую версию
echo "5. Запускаем новую версию..."
docker-compose -f docker-compose.reliable.yml up -d

# 6. Проверить статус
echo "6. Проверяем статус контейнеров..."
sleep 10
docker-compose -f docker-compose.reliable.yml ps

# 7. Проверить логи
echo "7. Проверяем логи..."
docker-compose -f docker-compose.reliable.yml logs --tail=20

# 8. Тестируем health endpoint
echo "8. Тестируем сервис..."
sleep 5
curl -f http://localhost:5001/health || echo "Health check failed"

echo ""
echo "✅ Развертывание завершено!"
echo "Сервис доступен на http://localhost:5001"
echo ""
echo "Для тестирования запустите:"
echo "python test_reliable_service.py"