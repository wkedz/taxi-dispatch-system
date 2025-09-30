curl -X POST http://localhost:8000/orders \
  -H 'content-type: application/json' \
  -d '{
    "user_id": 1,
    "start_x": 30,
    "start_y": 24,
    "end_x": 31,
    "end_y": 25
  }'
