# avl2gtfsrt-integration
Integration service for arbitrary GNSS tracker APIs to work with [avl2gtfsrt](https://github.com/sebastianknopf/avl2gtfsrt).

Currently, following providers are supported:

- [PAJ GPS](https://www.paj-gps.de/) (Adapter Name: `pajgps`)

## Installation
 
### Additional Requirements
The `avl2gtfsrt-integration` service requires requires a MQTT broker for the VDV435 communication and credentials for the API of the GNSS tracker API you want to integrate. See the list above for currently supported providers.

### Usage
To run the `avl2gtfsrt-integration` service, simply clone this repository to your destination:

```bash
git clone https://github.com/sebastianknopf/avl2gtfsrt-integration.git
cd avl2gtfsrt-integration
```

Then, configure all providers using the configuration YAML file. See [default.yaml](default.yaml) for reference. You can connect multiple providers with running one single `avl2gtfsrt-integration` service by configuring multiple instances.

Place the configuration file in the repositories directory and run:

```bash
pip install .
python -m avl2gtfsrt.integration run
```

### Use with Docker
Currently, the image is not published on dockerhub yet. You can build the container yourself locally by running:
```bash
docker build -t sebastianknopf/avl2gtfsrt-integration:latest .
```

Finally, you can run the docker container in detached mode with the mounted config file:
```bash
docker run --rm -it -d -v /your/path/to/config.yaml:/app/config.yaml sebastianknopf/avl2gtfsrt-integration:latest
```

## License
This project is licensed under the Apache License. See [LICENSE](LICENSE.md) for more information.