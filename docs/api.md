# API description

## Dispatcher

Here is the discription of Dispatcher API.

| Method and Endpoint                      | Description                       |
|------------------------------------------|-----------------------------------|
| POST /taxis/register                     | register taxi                     |
| POST /taxis/deregister                   | deregister taxi                   |
| POST /taxis/heartbeat                    | heartbeat for taxi                |
| GET /taxis/count                         | count of taxis                    |
| POST /orders                             | create trip                       |
| GET /orders/{trip_id}                    | trip details                      |
| POST /events/pickup                      | event picking up passanger        |
| POST /events/delivered                   | event delivering passanger        |
| GET /taxis                               | list of taxis                     |
| GET /trips                               | list of trips                     |
| GET /healtz                              | dispatcher status                 |

You can also use build-in docs of FastAPI (by default http://127.0.0.1:8000/docs)

## Taxi

Here is the discription of Taxi service API.

| Method and Endpoint                      | Description                       |
|------------------------------------------|-----------------------------------|
| GET /healtz                              | taxi status and its id            |
| POST /assign                             | assign trip to taxi               |

You can also use build-in docs of FastAPI (by default http://127.0.0.1:8081/docs only available by using `run make-taxi`)
