"""
Bayes sensor code split out from
https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/binary_sensor/bayesian.py

This module is used to explore the sensor.
"""
from collections import OrderedDict
from const import *


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

    return BayesianBinarySensor(
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


class BayesianBinarySensor(BinarySensorDevice):
    """Representation of a Bayesian sensor.
    Removed some methods I don't think will be needed for this investigation.
    """

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
        # return the entity_id to observ
        to_observe = set(obs['entity_id'] for obs in self._observations)
        self.entity_obs = dict.fromkeys(to_observe, [])
        # Append observations
        for ind, obs in enumerate(self._observations):
            obs['id'] = ind
            self.entity_obs[obs['entity_id']].append(obs)

        self.watchers = {
            'numeric_state': self._process_numeric_state,
            'state': self._process_state
        }

#    @asyncio.coroutine
    def async_added_to_hass(self):
        """Call when entity about to be added."""
        @callback
        # pylint: disable=invalid-name
        def async_threshold_sensor_state_listener(entity, old_state,
                                                  new_state):
            """Handle sensor state changes."""
            if new_state.state == STATE_UNKNOWN:
                return

            entity_obs_list = self.entity_obs[entity]

            for entity_obs in entity_obs_list:
                platform = entity_obs['platform']

                self.watchers[platform](entity_obs)

            prior = self.prior
            for obs in self.current_obs.values():
                prior = update_probability(
                    prior, obs['prob_true'], obs['prob_false'])
            self.probability = prior  # Updates prior for each observation.

    #        self.hass.async_add_job(self.async_update_ha_state, True)

        entities = [obs['entity_id'] for obs in self._observations]
#        async_track_state_change(
#            self.hass, entities, async_threshold_sensor_state_listener)

    def _update_current_obs(self, entity_observation, should_trigger):
        """Update current observation for single entity."""
        obs_id = entity_observation['id']

        if should_trigger:
            prob_true = entity_observation['prob_given_true']
            prob_false = entity_observation.get(
                'prob_given_false', 1 - prob_true)
            # Update prob_true and prob_false
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

    #@asyncio.coroutine
    def async_update(self):
        """Get the latest data and update the states."""
        self._deviation = bool(self.probability > self._probability_threshold)
