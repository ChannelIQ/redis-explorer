import redis
import os
import json
import datetime
import errno

class RedisDataManager:
    def __init__(self, host='localhost', port=6379, results_folder='~/redis-dumps/snapshots/'):
        self._rc = redis.Redis(host, port)
        self._results = os.path.expanduser(results_folder + str(datetime.datetime.utcnow()))


    def save_to_json(self, patterns, file_location=None):
        if file_location is None:
            file_location = self._results + '/dump.json'
        _mkdir_p(os.path.dirname(os.path.expanduser(file_location)))
        with open(os.path.expanduser(file_location), 'w') as f:
            json.dump(self.get_data(patterns), f)


    def load_from_json(self, file_location=None):
        if file_location is None:
            file_location = self._results + '/dump.json'
        with open(os.path.expanduser(file_location), 'r') as f:
            return json.load(f)


    def save_to_redis(self, keys, redis_client=None):
        if redis_client is None:
            redis_client = self._rc
        pipeline = redis_client.pipeline()
        for key in keys:
            key_type = keys[key]['type']
            if 'string' in key_type:
                pipeline.set(key, data[key]['val'])
            elif 'list' in key_type:
                for item in keys[key]['val']:
                    pipeline.rpush(key, item)
            elif 'zset' in key_type:
                for item in keys[key]['val']:
                    pipeline.zadd(key, item[0], item[1])
            elif 'set' in key_type:
                for item in keys[key]['val']:
                    pipeline.sadd(key, item)
            elif 'hash' in key_type:
                for field in keys[key]['val']:
                    pipeline.hset(key, field, keys[key]['val'][field])
        pipeline.execute()


    def get_data(self, patterns):
        return self._get_vals(self._get_types(self._get_keys(patterns)))


    def delete_matching_keys(self, patterns):
        self._del_keys(self._get_keys(patterns))


    def delete_keys(self, keys):
        self._del_keys(keys)

    def get_keys(self, patterns, with_types=False, sorted_by_key=False):
        if with_types:
            return self._get_types(self._get_keys(patterns, sorted_by_key=sorted_by_key), as_array=True)
        else:
            return self._get_keys(patterns, sorted_by_key=sorted_by_key)

    def _get_keys(self, patterns, sorted_by_key=False):
        pipeline = self._rc.pipeline()
        [pipeline.keys(pattern) for pattern in patterns]
        if sorted_by_key:
            return [item for sublist in pipeline.execute() for item in sorted(sublist)]
        else:
            return [item for sublist in pipeline.execute() for item in sublist]


    def _get_types(self, keys, as_array=False):
        pipeline = self._rc.pipeline()
        [pipeline.type(key) for key in keys]
        if as_array:
            return [dict({'key' : keys[index], 'type' : type}) for index, type in enumerate(pipeline.execute())]
        else:
            # Build return dictionary
            keysTypes = {}
            for index, type in enumerate(pipeline.execute()):
                keysTypes[keys[index]] = {
                    'type' : type,
                }
            return keysTypes


    def _get_vals(self, keys):
        pipeline = self._rc.pipeline()
        for index, key in enumerate(keys):
            key_type = keys[key]['type']
            if 'string' in key_type:
                pipeline.get(key)
            elif 'list' in key_type:
                pipeline.lrange(key, 0, -1)
            elif 'zset' in key_type:
                pipeline.zrange(key, 0, -1, withscores=True)
            elif 'set' in key_type:
                pipeline.smembers(key)
            elif 'hash' in key_type:
                pipeline.hgetall(key)
        vals = pipeline.execute()

        for index, key in enumerate(keys):
            keys[key]['val'] = vals[index]
        return keys


    def _del_keys(self, keys):
        pipeline = self._rc.pipeline()
        [pipeline.delete(key) for key in keys]
        pipeline.execute()

def _mkdir_p(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise
