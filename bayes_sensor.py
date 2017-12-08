"""
Bayes sensor code split out from
https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/binary_sensor/bayesian.py

This module is used to explore the sensor.
"""
from collections import OrderedDict

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

DEFAULT_NAME = "Bayesian Binary Sensor"
DEFAULT_PROBABILITY_THRESHOLD = 0.5

VALID_CONFIG = {
    CONF_PRIOR: 0.1,
    CONF_NAME: 'test_name',
    CONF_PROBABILITY_THRESHOLD: 0.95,
    CONF_DEVICE_CLASS: 'binary_device',
    CONF_OBSERVATIONS:[
        {
        CONF_ENTITY_ID: 'switch.kitchen_lights',
        CONF_P_GIVEN_T: 0.6,
        CONF_P_GIVEN_F: 0.2,
        CONF_PLATFORM: 'state',
        CONF_TO_STATE: 'on'}]
        }


def update_probability(prior, prob_true, prob_false):
    """Update probability using Bayes' rule."""
    numerator = prob_true * prior
    denominator = numerator + prob_false * (1 - prior)

    probability = numerator / denominator
    return probability


def setup_platform(config):
    """Set up the Bayesian Binary sensor.
    Modified from async_setup_platform."""
    name = config[CONF_NAME]
    observations = config[CONF_OBSERVATIONS]
    prior = config[CONF_PRIOR]
    probability_threshold = config[CONF_PROBABILITY_THRESHOLD]
    device_class = config[CONF_DEVICE_CLASS]

    return    BayesianBinarySensor(
            name, prior, observations, probability_threshold, device_class)


class BinarySensorDevice():  # Entity
    """Represent a binary sensor."""

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return None

    @property
    def state(self):
        """Return the state of the binary sensor."""
        return STATE_ON if self.is_on else STATE_OFF

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return None


class BayesianBinarySensor():  # BinarySensorDevice
    """Representation of a Bayesian sensor.
    Removed some methods I don't think will be needed for this investigation."""

    def __init__(self, name, prior, observations, probability_threshold,
                 device_class):
        """Initialize the Bayesian sensor."""
        self._name = name
        self._observations = observations
        self._probability_threshold = probability_threshold
        self._device_class = device_class
        self._deviation = False
        self.prior = prior
        self.probability = prior

        self.current_obs = OrderedDict({})

        to_observe = set(obs['entity_id'] for obs in self._observations)  # return the entity_id to observ

        self.entity_obs = dict.fromkeys(to_observe, [])

        for ind, obs in enumerate(self._observations):
            obs['id'] = ind
            self.entity_obs[obs['entity_id']].append(obs)

        self.watchers = {
            'numeric_state': self._process_numeric_state,
            'state': self._process_state
        }

    def _update_current_obs(self, entity_observation, should_trigger):
        """Update current observation."""
        obs_id = entity_observation['id']

        if should_trigger:
            prob_true = entity_observation['prob_given_true']
            prob_false = entity_observation.get(
                'prob_given_false', 1 - prob_true)

            self.current_obs[obs_id] = {
                'prob_true': prob_true,
                'prob_false': prob_false
            }

        else:
            self.current_obs.pop(obs_id, None)

    def _process_numeric_state(self, entity_observation):
        """Add entity to current_obs if numeric state conditions are met."""
        entity = entity_observation['entity_id']

        should_trigger = condition.async_numeric_state(
            self.hass, entity,
            entity_observation.get('below'),
            entity_observation.get('above'), None, entity_observation)

        self._update_current_obs(entity_observation, should_trigger)

    def _process_state(self, entity_observation):
        """Add entity to current observations if state conditions are met."""
        entity = entity_observation['entity_id']

        should_trigger = condition.state(
            self.hass, entity, entity_observation.get('to_state'))

        self._update_current_obs(entity_observation, should_trigger)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._deviation

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_class(self):
        """Return the sensor class of the sensor."""
        return self._device_class

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_OBSERVATIONS: [val for val in self.current_obs.values()],
            ATTR_PROBABILITY: round(self.probability, 2),
            ATTR_PROBABILITY_THRESHOLD: self._probability_threshold,
        }
