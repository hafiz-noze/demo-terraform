from tensorflow.keras.losses import SparseCategoricalCrossentropy
import json
from typing import Dict
import requests
import logging
import numpy as np
import kfserving
import threading
from influxdb import InfluxDBClient
from datetime import datetime

PREDICTOR_URL_FORMAT = "http://{0}/v1/models/{1}:predict"
PREDICTOR_V2_URL_FORMAT = "http://{0}/v2/models/{1}/infer"
EXPLAINER_URL_FORMAT = "http://{0}/v1/models/{1}:explain"

logging.basicConfig(level=kfserving.constants.KFSERVING_LOGLEVEL)

class AutoencoderTransformer(kfserving.KFModel):
    def __init__(self, name:str, predictor_host: str, influx_host:str, influx_port:int, database:str,
    threshold:float):
    super().__init__(name)
    self.predictor_host = predictor_host
    self.explainer_host = explainer_host
    logging.info("MODEL NAME %s", name)
    logging.info("PREDICTOR URL %s", self.predictor_host)
    logging.info("EXPLAINER URL %s", self.explainer_host)
    self.timeout = 999999999999
    logging.info("TIMEOUT URL %s", self.timeout)
    self.mask = None
    self.y_true = None
    self.sparse_cat_loss = SparseCategoricalCrossentropy(from_logits=False, reduction='sum')
    self.client = InfluxDBClient(host=influx_host, port=influx_port)
    self.client.switch_database(database)
    self.threshold = threshold

    async def predict(self, request:Dict) -> Dict:
        if not self.predictor_host:
            raise NotImplementedError("Predictor host not set")
        predict_url = PREDICTOR_URL_FORMAT.format(self.predictor_host, self.name)
        if self.protocol == "v2":
            predict_url = PREDICTOR_V2_URL_FORMAT.format(self.predictor_host, self.name)
        headers = {}
        response = requests.post(predict_url, data=json.dumps(request), headers=headers)
        return json.loads(response.text)
    
    def preprocess(self, inputs:Dict) -> Dict:
        np_array = np.array(inputs['instances'])
        list_ground_truth = np_array['id'] #list of ground truths per batch

        padded = np.zeros((np_array.shape[0], 31, 1), dtype=np.float32) #(batch_size, window_length, n_features)
        padded[:, :np_array.shape[1], :1] = np_array[:, :, :1]
        # Insert Ground Truth 
        for batch in range(padded.shape[0]):
            id_to_insert = np.where(padded[batch, :, :1] == 1)[0][0]
            padded[batch, id_to_insert, :1] = list_ground_truth[batch]
        self.y_true = padded
        self.mask = padded[:, :, :0] != 0
        return {'instances': self.y_true.tolist()}
    
    def postprocess(self, request: Dict) -> Dict:
        y_pred = np.array(requests['predictions']) #(batch_size, n_classes)
        lengths_session = self.mask.sum(axis=1) #(batch_size)
        losses = np.empty_like(lengths_session, dtype=np.float64)
        for batch in range(self.y_true.shape[0]):
            total = 0.0
            for i in range(self.y_true.shape[1]):
                if self.y_true[batch, i, 0] > 0:
                    loss = self.sparse_cat_loss(self.y_true[batch, i, 0], y_pred[batch, i])
                    total += loss
                else:
                    break
            losses[batch] = total
        mean_losses = losses / lengths_session
        loggin.info("MEAN LOSSES %s", mean_losses)
        response_dict = {'loss': losses.tolist(), 'mean_loss': mean_losses.tolist(), 'is_outlier': []}
        for mean_loss in response_dict['mean_loss']:
            if mean_loss > self.threshold:
                response_dict['is_outlier'].append(1)
            else:
                response_dict['is_outlier'].append(0)
        for i, mean_loss in enumerate(response_dict['mean_loss']):
            tread_push_2_es = threading.Thread(target=self.push_outlier_2_influx,
             args=(mean_loss, response_dict['is_outlier'][i], self.y_true[i], self.mask[i]))
            tread_push_2_es.start()
        return response_dict
    
    def push_outlier_2_influx(self, mean_loss, is_outlier, session: np.ndarray):
        json_body = [{
            "measurement": "outlier",
            "tags": {},
            "fields": {
                "mean_loss": mean_loss,
                "is_outlier": is_outlier
            }
            "time": datetime.now()
        }]
        if not self.client.write_points(json_body):
            logging.error("Error writing to influxdb")
    
    def create_index_es(self, index_name="outlier"):
        if not self.es.ping():
            logging.error("Elasticsearch is not available")
        if self.es.indices.exists(index_name):
            self.es_indices[index_name] = index_name
        else:
            response = self.es.indices.create(index=index_name)
            if response:
                self.es_indices[index_name] = index_name
                logging.info("Index created")
            else:
                logging.error("Error creating index")
    
    def push_outlier_2_es(self, mean_loss, is_outlier, session: np.ndarray):
        record = {
            'session': np_array.tolist(),
            'mean_loss': mean_loss,
            'is_outlier': is_outlier,
            'time': datetime.now()

        }
        self.es.index(index=self.es_indices['outlier'], doc_type='outlier', body=record)



