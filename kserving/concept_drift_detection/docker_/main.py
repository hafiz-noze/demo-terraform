import argparse
import imp
import logging
import kfserving
from concept_drift_model import ConceptDriftModel


logging.basicConfig(level=kfserving.constants.KFSERVING_LOGLEVEL)

DEFAULT_MODEL_NAME = 'concept-drift'
DEFAULT_INFLUX_HOST = 'release-influxdb.default.svc.cluster.local'
DEFAULT_INFLUX_PORT = 8086
DEFAULT_INFLUX_DATABASE = 'metrics'
DEFAULT_MODEL_PATH = './model'

parser = argparse.ArgumentParser(parents=[kfserving.kfserver.parser])

parser.add_argument('--model_name', default=DEFAULT_MODEL_NAME,
                    help='The name that the model is served under.')

parser.add_argument('--influx_host', default=DEFAULT_INFLUX_HOST,
                    help='InfluxDB Host')

parser.add_argument('--influx_port', default=DEFAULT_INFLUX_PORT,
                    help='InfluxDB Port')
parser.add_argument('--influx_database', default=DEFAULT_INFLUX_DATABASE,
                    help='InfluxDB Database')
parser.add_argument('--model_path', default=DEFAULT_MODEL_PATH,
                    help='Concept Drift Model Path')
args, _ = parser.parse_known_args()

if __name__ == "__main__":
    model = ConceptDriftModel(
        args.model_name,
        args.model_path,
        args.influx_host,
        args.influx_port,
        args.influx_database

    )
    model.load()

    server = kfserving.KFServer(
        http_port = "<port_number>",
        max_buffer_size = "<max_buffer_size>",
        workers = 1
    )

    logging.info("BUFFER SIZE %s", server.max_buffer_size)
    server.start(models=[model])