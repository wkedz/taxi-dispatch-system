# Taxi Dispatch System

System for distributing taxis for cleints.

## Requirements
- Python **3.12**
- Docker + Docker Compose
- Make
- uv

## Deploying

### Localhost deployment

Install all packages

```bash
make install
```

Run all services locally

```bash
make run-all
```

Run single service:

```bash
make run-dispatcher
make run-taxi
make run-client
make run-grid
make run-db
```

Stop all services:

```bash
make stop-all
```

### Docker deployment

Build container images:

```bash
make run-docker-rebuild
```

Run all containers:

```bash
make run-docker-all
```

Run rebuild of images:

```bash
make run-docker-rebuild
```

Run single service container:

```bash
make run-docker-dispatcher
make run-docker-taxi
make run-docker-client
make run-docker-grid
make run-docker-db
```

Stop containers:

```bash
make stop-docker
```

## Scaling taxis

In order to scale number of taxis modify field `deploy.replicas = NUMBER-OF-REPLICAS`.

## Visualization

In order to check to flow of services pleas run grid service `make run-grid` or `make run-docker-grid` and go to `http://localhost:8082/` (by default).

## More info

For more info please check following references:

[architecture](./docs/architecture.md)

[api](./docs/api.md)

## Setting env

There is an .env.example file, with all ENV variables that are used during deployment. You can modify values of those ENV variables.

## Testking

In order to run test, please do the following:

```bash
make install-dev
make run-tests
```

## Help

For more info, pleas run help.

```bash
make help
```