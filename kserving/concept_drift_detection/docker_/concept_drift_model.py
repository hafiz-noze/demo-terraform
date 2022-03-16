import re
import tensorflow as tf
import numpy as np
import json
import tornado
import logging
import kfserving
import threading
from typing import Dict 
from albi_detect.utils.saving import load_detector
from albi_detect.cd import KSDrift, MMDrift
from influxdb import InfluxDBClient
from datetime import datetime

PREDICTOR_URL_FORMAT = "http://{0}/v1/models/{1}:predict"
PREDICTOR_V2_URL_FORMAT = "http://{0}/v2/models/{1}/infer"
EXPLAINER_URL_FORMAT = "http://{0}/v1/models/{1}:explain"

logging.basicConfig(level=kfserving.constants.KFSERVING_LOGLEVEL)

class ConceptDriftModel(kfserving.KFModel):
    """ A class for the data handling activities of concept drift task
    and a KFServing compatible response.

    Agrs:
        kfserving (class object): The KFModel class from the KFServing library.
    """
    def __init__(self, name:str, influx_host:str, influx_port:int, database:str,
                    model_path:str):
        """ Initialize the ConceptDriftModel class.
            
            Args:
                name (str): The name of the model.
        """
        super().__init__(name)
        self.timeout = 999999999999
        logging.info("TIMEOUT URL %s", self.timeout)
        self.name = name
        self.batch_size = 100
        self.batches = None
        self.model = None
        # influxDB Client
        self.client = InfluxDBClient(host=influx_host, port=influx_port)
        self.client.switch_database(database)
        self.model_path = model_path

    def load(self):
        self.model = load_detector(self.model_path)
        self.ready = True
    
    async def predict(self, request:Dict) -> Dict:
        if self.batches.shape[0] >= self.batch_size:
            preds_ood = self.model.predict(self.batches, return_p_val=True)
            logging.info("Drift %s", preds_ood['data']['is_drift'])
            thread_push_2_influx = threading.Thread(target=self.push_conceptdrift_2_influx,
                                                    args=[preds_ood['data']['is_drift']])
            thread_push_2_influx.start()
            self.batch = None
            preds_ood["data"]["distance"] = preds_ood["data"]["distance"].tolist()
            preds_ood['data']['p_val'] = preds_ood['data']['p_val'].tolist()
        else:
            preds_odd = {}
        return preds_ood

def preprocess(self, inputs:Dict) -> Dict:
    """ Preprocess the inputs to the model.
    """
    np_array = np.array(inputs['instances'])
    list_ground_truth = inputs['id']
    padded = np.zeros((np_array.shape[0], 31, 1), dtype=np.float32)
    padded[:, :np_array.shape[1], :1] = np_array[:, :, :1]
    for batch in range(padded.shape[0]):
        id_to_insert = np.where(padded[batch, :, :1] == 0)[0][0]])
        padded[batch, id_to_insert, :1] = list_ground_truth[batch]
    if self.batches is None:
        self.batches = padded[:, :, :1]
    else:
        self.batches = np.concatenate([self.batches, padded[:, :, :1]], axis=0)
    return inputs

def postprocess(self, request:Dict) -> Dict:
    return request


def push_conceptdrift_2_influx(self, is_concept_drift:int):
    json_body = [
        "measurement": "concept_drift",
        "tags": { },
        "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "fields": {
            "is_concept_drift": is_concept_drift
        }
    ]

    if not self.client.write_points(json_body):
        logging.error("COULD NOT WRITE DATA INTO INFLUXDB!")

def create_index_es(self, index_name='concept_drift'):
    if not self.es.ping():
        logging.error("ELASTICSEARCH IS DOWN!")
    if self.es.indices.exists(index_name):
        logging.info("INDEX %s ALREADY EXISTS!", index_name)
    else:
        response = self.es.indices.create(index=index_name)
        if response:
            self.es_indices[index_name] = index_name
            logging.info("INDEX %s CREATED!", index_name)
        else:
            logging.error("COULD NOT CREATE INDEX %s!", index_name)

def push_conceptdrift_2_es(self, is_concept_drift:int):
    record = {
        "is_concept_drift": is_concept_drift,
        "timestamp": datetime.now(),
    }
    self.es.index(index='concept_drift', doc_type='concept_drift', body=record)