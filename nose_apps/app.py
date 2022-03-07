from envs import env
import logging
import datetime
import random
import traceback
import time
import json
import requests
from azure.storage.blob import BlobServiceClient

def _add_final_output(result_dict, names, outputs):
    offsets = [
        # env('CO2_OFFSET', var_type="float", allow_none=False),
        0.0, #no2
        0.0, #nh3
        0.0, #tvoc
        0.0, #butanal
        0.0, #formaldehyde
        0.0, #nicotine
        0.0, #ethanol
        0.0 #nitric oxide
        ]
    for i, name in enumerate(names):
        result_dict[name] = outputs[i]
        result_dict[name] += offsets[i]
        # if result_dict[name] < 0:
        #     result_dict[name] = 0.0
    # if result_dict["carbon_dioxide"] <= 400.0:
    #     result_dict["carbon_dioxide"] = 400.0 + random.uniform(-20.0, 20.0)
    # elif result_dict["carbon_dioxide"] >= 2000.0:
    #     result_dict["carbon_dioxide"] = 2000.0 + random.uniform(-50.0, 50.0)
    if result_dict["nitrogen_dioxide"] <= 0.0:
        result_dict["nitrogen_dioxide"] = 0.0
    elif result_dict["nitrogen_dioxide"] >= 10.0:
        result_dict["nitrogen_dioxide"] = 10.0 + random.uniform(-1.0, 1.0)
    if result_dict["ammonia"] <= 0.0:
        result_dict["ammonia"] = 0.0
    elif result_dict["ammonia"] >= 75.0:
        result_dict["ammonia"] = 75.0 + random.uniform(-3.0, 3.0)
    if result_dict["butanal"] <= 0.0:
        result_dict["butanal"] = 0.0
    elif result_dict["butanal"] >= 50.0:
        result_dict["butanal"] = 50.0 + random.uniform(-3.0, 3.0)
    if result_dict["nicotine"] > 1.0:
        result_dict["nicotine"] = 1.0
    elif result_dict["nicotine"] < 0.0:
        result_dict["nicotine"] = 0.0
    for chemical in ["tvoc", "formaldehyde", "ethanol", "nitric_oxide"]:
        if result_dict[chemical] <= 0.0:
            result_dict[chemical] = 0.0
    # for chemical in ["butanal", "formaldehyde"]:
    #     result_dict[chemical] = 0.0
    return result_dict #


def _reset_states(cached_h1, cached_c1, cached_h2, cached_c2, analytes, device_id, reason=""):
    for analyte in analytes:
        if analyte in ["co2", "nh3", "no", "nicotine"]:
            num_cells = 20
        elif analyte in ["c4h8o", "etoh"]:
            num_cells = 200
        elif analyte == "no2":
            num_cells = 32
        elif analyte == "ch2o":
            num_cells = 128
        else:
            num_cells = 12
        cached_h1[analyte] = [0.0] * num_cells
        cached_c1[analyte] = [0.0] * num_cells
        cached_h2[analyte] = [0.0] * num_cells
        cached_c2[analyte] = [0.0] * num_cells
    cache.set(key="cached_h1", value=cached_h1)
    cache.set(key="cached_c1", value=cached_c1)
    cache.set(key="cached_h2", value=cached_h2)
    cache.set(key="cached_c2", value=cached_c2)
    logging.info("STATE MATRICES HAVE BEEN RESET FOR {} DUE TO {}".format(device_id, reason))
    return cached_h1, cached_c1, cached_h2, cached_c2


def process(device_id: str, measurements: list, sensor_module_id: str):

    app_settings = {
        "BASELINE_LENGTH": env("BASELINE_LENGTH", var_type="int", allow_none=False),
        "APPLICATION_CACHE_KEY": env("APPLICATION_CACHE_KEY", var_type="str", allow_none=False),
        "BASELINE_CONNECTION_STRING": env("BASELINE_CONNECTION_STRING", var_type="str", allow_none=False)
    }

    rpc_device_name = measurements["rpc_device_name"]
    cache.set_cache_key(app_settings["APPLICATION_CACHE_KEY"], device_id=device_id)

    cache.set(key="sensor_module_id", value=sensor_module_id)
    cache.set(key="rpc_device_name", value=rpc_device_name, ex=None)

    analytes = ["no2", "nh3", "tvoc", "c4h8o", "ch2o", "nicotine", "etoh", "no"]
    # names = ["carbon_dioxide", "nitrogen_dioxide", "ammonia", "tvoc", "butanal"]
    names = ["nitrogen_dioxide", "ammonia", "tvoc", "butanal", "formaldehyde", "nicotine", "ethanol", "nitric_oxide"]

    norms = []
    frequency = []

    counter_reset = 1

    for val in frequency:
        counter_reset *= val
    counter = cache.get(key="counter") or 0
    if counter % counter_reset == 0:
        logging.info("Resetting counter of {} for {}".format(counter, device_id))
        counter = 0
    counter += 1
    cache.set(key="counter", value=counter)

    preds = dict()
    previous_results = cache.get(key="previous_results") or None

    cached_h1 = cache.get(key="cached_h1") or dict()