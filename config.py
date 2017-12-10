"""
Config for use with bayes_sensor
"""
from const import *

VALID_CONFIG = {
    CONF_PRIOR: 0.25,
    CONF_NAME: 'in_bed',
    CONF_PROBABILITY_THRESHOLD: 0.95,
    CONF_DEVICE_CLASS: 'binary_device',
    CONF_OBSERVATIONS: [
        {
            CONF_ENTITY_ID: 'sensor.bedroom_motion',
            CONF_P_GIVEN_T: 0.5,
            CONF_PLATFORM: 'state',
            CONF_TO_STATE: 'on'},
        {
            CONF_ENTITY_ID: 'sun.sun',
            CONF_P_GIVEN_T: 0.7,
            CONF_PLATFORM: 'state',
            CONF_TO_STATE: 'below_horizon'}]
        }
