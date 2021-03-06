# Cambridge Python Smart Sensor Framework

This framework is designed for sensors that send their data back in real-time, to be processed immediately in
the receiving system.

## Key concepts:

*real-time*: This is the concept of processing information without delay. The typical default behaviour of sensors
to send their data periodically, say once a minute (or whatever) automatically introduces a possible delay of, say, 59 seconds
for an important reading. Attempting to address this problem by simply tweaking the transmit period is lazy and ultimately
ineffective.

*readings*: The actual sensor measurements, taken as frequently as is reasonable. I.e. the sensor will typically
be able to measure stuff more frequently than it might be expected to send it back to a server. Most sensors today
periodically (once a second, once a minute, once an hour, or whatever) send their most recent reading (or some
average, or other derived value) back to a server where it can be stored for programs or people later to look at
it. We can do better than that, and *immediately* send information as soon as it seems relevant

*events*: This is the essential advance in the framework, with the expectation the sensor is designed to be
smart enough to recognize meaningful situations reflected by the sensor readings. Examples for the Cambridge
Coffee Pot include a new pot of coffee, or the pot becoming empty, or someone taking a cup of coffee from the
pot. These events can be transmitted *immediately* in contrast to the generic 'sensor readings' which may be
reported periodically.

*feedhandler*: This is a component of the receiving application system that is designed to process the
incoming data (particularly the *events*) in real-time. I.e. there is no delay built into the system as a
result of the receiving application simply *storing* the data in the hope that some subsequent process will
query the data and process it. The vast majority of existing systems process incoming data by storing it (e.g.
a customer order, a traffic light failure report), with separate program periodically checking to see if any
customers have ordered anything or any traffic lights have been reported broken.

## Directories

`cambridge_coffee_pot/code` contains `main.py`, the main program to run the sensor.

`cambridge_coffee_pot/code/classes` contains the various Python classes that define the sensor, such as `WeightSensor`.
.
`cambridge_coffee_pot/code/config` contains JSON configuration files i.e. startup settings are in:
```
cambridge_coffee_pot/code/config/sensor_config.json
```
The sensor may persist values (like the 'tare' reading for the load cells) into the `cambridge_coffee_pot/config`
directory.

`cambridge_coffee_pot/code/st7735_ijl20` contains the library classes for the LCD display and emulator.

`cambridge_coffee_pot/code/hx711_ijl20` contains the library classes for the load cells.

## main.py

Provides the outermost application code which instantiates the required classes (i.e. Config, Sensor)
and loops loading sensor readings and processes each reading.

## config.py

Creates a Config() object with a 'settings' dictionary with values loaded from a provided filename.

## sensor.py

Stores the loaded data in a TimeBuffer.

Provides the `process_sample` function to process the data, which will look at the current value and
also some range of previous values to decide whether an EVENT has occurred.

## weight_sensor.py

Links to the required libraries and reads the data from the load cell sensors.

## display.py

Links the required libraries and writes on the LCD display (or an emulated one).

## sensor_utils.py

Contains generally useful functions and classes, such as `string = list_to_string(list)`.

## time_buffer.py

Implements a circular buffer of <*time*, *value*> pairs which can be stored and retrieved with
`put` and `get` and also useful functions are provided which operate in the time dimension, e.g.
finding the median value over a time period.

For development and debug purposes the TimeBuffer provides complimentary `load(filename)` and
`save(filename)` methods which can persist a buffer of timestamped readings to a file and reload
them, plus a `play(callback)` method which can replay sensor readings through your code (see `test.py`).

### Create a TimeBuffer

E.g.
```
buffer = TimeBuffer(buffer_size)
```

The argument to TimeBuffer is `buffer_size` i.e. how many entries you wish to store (the buffer will always
contain the latest `buffer_size` (or fewer) entries).

### Store a reading in the TimeBuffer

```
buffer.put(timestamp, value)
```

`timestamp` is a *float* unix timestamp, e.g. 1574506065.345123 where the integer part is seconds since the
beginning of time (which Computer Scientists believe was 1st Jan 1970).

`value` can be any value although methods such as `median` (see below) will assume the value is a number.

### Retrieve a reading from the timebuffer

```
foo = buffer.get(index_offset)
```

`index_offset` is a positive index in the buffer where `0` means the latest reading, `1` means the
penultimate reading and so on. The index_offset may refer to a buffer position outside the currently
stored set of readings or is outside the range of the buffer (e.g. you `buffer.get(100)` when you
have only stored 50 readings so far, or the buffer size is less than 100) in which case the method
will return `None`.

For a successful `get`, the returned value will be a Python `<time, value>` dictionary e.g.

```
{ "ts": 1574506065.345123, "value": 42.0 }
```

The latest sample reading (assuming at least one has been stored) can always be retrieved at `buffer.get(0)`.

### Persist the current TimeBuffer contents to a file

```
buffer.save(filename)
```

This will overwrite or create a CSV file of `<time,value>` pairs, e.g. see `../data/2019-11-22_readings.csv`.

### Load a TimeBuffer from a file

```
buffer.load(filename)
```

This will get the buffer back to the state it was in when you (typically) did the `buffer.save(filename)`. As the
file format is generically simple CSV, the data file can be created by any method outside of Python.

The `load` method will ignore lines in the file that don't parse into a comma-separated pair of values.

### Replay data from the TimeBuffer

```
buffer.play(callback)
```

This will iterate through the `<time,value>` samples in the TimeBuffer and call the `callback` with each sample, i.e.
`callback` will be a function accepting a timestamp and value as arguments such as in Sensor:

```
def process_sample(timestamp, value)
    ...
```

Which might be called for each sample in the TimeBuffer via:

```
s = Sensor(config)

buffer.play(s.process_sample)
```

Note this data is *not* played back in real time, it is iterated as fast as the callback code will allow with the processing
function being given *both* the time and the reading value such that temporal pattern recognition can work as in the real
sensor.

## TimeBuffer Pattern recognition functions

### Find position of samples in buffer a time offset from the latest sample

```
offset = buffer.time_to_offset(time_offset)
```

Will return the index offset for the newest reading in the TimeBuffer that is *older* than the time of the
latest sample minus the `time_offset` in seconds.

Will return `None` if no reading is found (i.e. the `time_offset` is before the earliest reading in the TimeBuffer)

### Find the median value of a set of values in the TimeBuffer

```
value, next_offset, actual_duration, sample_count = buffer.median(index_offset, duration)
```

Will return the median value of a set of readings in the TimeBuffer.

`duration` is a period in *seconds* over which the median is to be found which will run up to the offset given.

The most typical initial usage is expected to be with an offset of `0`, i.e. your program will be counting backwards from
the most recent data sample, e.g. `buffer.median(0, 1)` will return the median value of the readings for the past one second
up to and including the most recent reading.

These functions return a tuple `<median value, next_offset>` where `next_offset` is the index offset into the buffer that
precedes the oldest data sample within the given 'duration'. This provides an efficiency benefit if an immediately following
call will be intended to calculate a median for a duration preceding this first calculation. For example:
```
median_1, offset_1 = buffer.median(0,2)
if not median_1 == None:
    median_2, offset_2 = buffer.median(offset_1, 3)
```
This will provide `median_1` and `median_2` for the data samples from the most recent 2 seconds, and preceding 3 seconds in the
buffer. For the coffee pot a transition from approximately zero to approximately 3400 would suggest a new fresh pot of coffee has
appeared.

### Find the mean value of a set of values in the TimeBuffer

```
value, next_offset, actual_duration, sample_count = buffer.mean(index_offset, duration)
```

Similar functions to `median` above, but returning the mean value.

### Find the deviation of a set of values relative to a given value

Returns the square root of ( the sum of the squared differences between each sample value
and the provided `mean_value` ). I.e. will be the Standard Deviation if the provided `mean_value` is
the arithmetic mean.

```
value, next_offset, actual_duration, sample_count = buffer.deviation(index_offset, duration, mean_value)
```

### Search the buffer to find if a sample matches a provided test function

Returns a tuple (Sample, ...) or (None, ...) depending on whether a provided function returns True
for any sample in the buffer over the duration given.

```
sample, next_offset, actual_duration, sample_count = buffer.find(offset, duration, test_function)
```

The `test_function` will be called with a sample (i.e. `{ "ts": , "value" }`) and should return `True`
or `False`. For example, if the buffer contains values of the form `{ "weight": 99, "confidence": 0.5 }` and
you want to know if the weight value was below 50 in the past 5 seconds:
```
def low_weight(sample):
    return sample['value']['weight] < 50

buffer.test(0,5,low_weight)
```
An inline function could also have been used, i.e. 
```
buffer.test(0, 5, lambda sample: sample['value']['weight']<50)
```

## Sensor and TimeBuffer replay of data

See `test.py`

```
import sys

from classes.time_buffer import TimeBuffer

from classes.config import Config

from classes.sensor import Sensor

from classes.sensor_utils import list_to_string

print("test.py started with {} arguments: [{}]".format(len(sys.argv), list_to_string(sys.argv)))

if len(sys.argv) > 1 :
    filename = sys.argv[1]
    config = Config(filename)
else:
    config = Config(None)

config.settings["VERSION"] = "TEST_0.1"

s = Sensor(settings = config.settings)

s.begin()

# for playback we can specify
#   sleep=0.1 for a fixed period between samples
# or
#   realtime=True which will pause the time between recorded sample timestamps.
# otherwise the playback will be as fast as possible.

t = TimeBuffer(settings=config.settings)

t.load('../data/2019-11-22_readings.csv')

t.play(s.process_sample, realtime=True)

```

