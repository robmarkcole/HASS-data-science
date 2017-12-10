"""
Constants required for bayes_sensor.py
"""

ATTR_OBSERVATIONS = 'observations'
ATTR_PROBABILITY = 'probability'
ATTR_PROBABILITY_THRESHOLD = 'probability_threshold'

CONF_OBSERVATIONS = 'observations'
CONF_PRIOR = 'prior'
CONF_PROBABILITY_THRESHOLD = 'probability_threshold'
CONF_P_GIVEN_F = 'prob_given_false'
CONF_P_GIVEN_T = 'prob_given_true'
CONF_TO_STATE = 'to_state'

CONF_DEVICE_CLASS = 'device_class'
CONF_ENTITY_ID = 'entity_id'  # These are HA defaults
CONF_NAME = 'name'
CONF_PLATFORM = 'platform'

STATE_ON = 'on'
STATE_OFF = 'off'
STATE_UNKNOWN = 'unknown'

DEFAULT_NAME = "Bayesian Binary Sensor"
DEFAULT_PROBABILITY_THRESHOLD = 0.5
