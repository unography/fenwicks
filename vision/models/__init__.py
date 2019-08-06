import keras_applications

from tensorflow.python.keras import backend
from tensorflow.python.keras import engine
from tensorflow.python.keras import layers
from tensorflow.python.keras import models
from tensorflow.python.keras import utils
from tensorflow.python.util import tf_inspect


def keras_modules_injection(base_fun):
  """Decorator injecting tf.keras replacements for Keras modules.
  Arguments:
      base_fun: Application function to decorate (e.g. `MobileNet`).
  Returns:
      Decorated function that injects keyword argument for the tf.keras
      modules required by the Applications.
  """

  def wrapper(*args, **kwargs):
    kwargs['backend'] = backend
    if 'layers' not in kwargs:
      kwargs['layers'] = layers
    kwargs['models'] = models
    kwargs['utils'] = utils
    return base_fun(*args, **kwargs)
  return wrapper
