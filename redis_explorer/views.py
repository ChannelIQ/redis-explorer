from flask import render_template, request
from redis_explorer import app
import redis, time, json
import redisdatamanager as rdm

ENVS_FILE = 'redis_explorer/envs.json'
ENVS = json.load(open(ENVS_FILE))

@app.context_processor
def inject_envs():
    return dict(envs=ENVS)

@app.route('/')
def display_index():
    rc = _get_host_and_port(request)
    info = rc.info()
    return render_template('index.html', info=info)

@app.route('/environments/', methods=['GET', 'POST'])
def display_environments():
    if request.method == 'POST':
        if 'delete' in request.form:
            ENVS['environments'].pop(request.form['env'])
            with open(ENVS_FILE, 'w') as f:
                json.dump(ENVS, f)
        if 'add_host' in request.form:
            ENVS['environments'][request.form['name']] = {
                'host' : request.form['host'],
                'port' : request.form['port']
            }
            with open(ENVS_FILE, 'w') as f:
                json.dump(ENVS, f)
    return render_template('envs.html')

@app.route('/search/', methods=['GET', 'POST'])
def display_search():
    redis_manager = _get_rdm(request)
    if request.method == 'POST':
        if 'delete' in request.form:
            redis_manager.delete_keys(request.form.getlist('queryResultRow'))
        if 'download' in request.form:
            return 'not implemented yet'
        return render_template('search.html')
    else:
        key_pattern = request.args.get('key_pattern', '')
        key_patterns = request.args.get('key_patterns', '')
        if key_pattern or key_patterns:
            patterns = key_pattern
            if key_patterns:
                if 'stripQuotes' in request.args:
                    key_patterns = key_patterns.replace('"', '')
                delimitor = request.args.get('delimitor', '')
                if 'space' in delimitor:
                    patterns = key_patterns.split(' ')
                if 'comma' in delimitor:
                    patterns = key_patterns.split(',')
                else:
                    patterns = key_patterns.split(' ')
            start_time = time.time()
            keys = redis_manager.get_keys(patterns, with_types=True, sorted_by_key=True)
            end_time = time.time()
            return render_template('keys.html', keys=keys, key_pattern=' '.join(patterns), query_time=(end_time - start_time))
        else:
            return render_template('search.html')

@app.route('/view/<key>', methods=['GET', 'POST'])
def display_key(key):
    redis_client = _get_host_and_port(request)
    key_type = redis_client.type(key)
    if request.method == 'POST':
        key_type = request.form['type']
        _form_handler(redis_client, key, key_type, request)
    item = _prepare_item(key, request, key_type=key_type, redis_client=redis_client)
    return render_template('object_pages/{0}.html'.format(key_type), item=item, type=key_type, key=key)

@app.route('/primitive/<key>')
def provide_primitive(key):
    redis_client = _get_host_and_port(request)
    key_type = redis_client.type(key)
    item = _prepare_item(key, request, key_type=key_type, redis_client=redis_client)
    return render_template('object_types/{0}.html'.format(key_type), item=item)

##################
# Primitive Prep #
##################

def _prepare_item(key, request, key_type='unknown', redis_client=None):
    if redis_client is None:
        redis_client = _get_host_and_port(request)
    if 'unknown' in key_type:
        keyType = redis_client.type(key)
    if 'list' in key_type:
        return _prepare_list(key, redis_client)
    if 'zset' in key_type:
        return _prepare_zset(key, redis_client)
    if 'set' in key_type:
        return _prepare_set(key, redis_client)
    if 'hash' in key_type:
        return _prepare_hash(key, redis_client)
    if 'string' in key_type:
        return _prepare_string(key, redis_client)

def _prepare_string(string_key, rc):
    return rc.get(string_key)

def _prepare_list(list_key, rc):
    r_list = []
    for key in reversed(rc.lrange(list_key, 0, -1)):
        item = {
            'key' : key,
            'type' : rc.type(key),
        }
        r_list.append(item)
    return r_list

def _prepare_zset(zset_key, rc):
    r_set = []
    for member in rc.zrange(zset_key, 0, -1, withscores=True):
        item = {
            'key' : member[0],
            'score': member[1],
            'type' : rc.type(member[0]),
        }
        r_set.append(item)
    return r_set

def _prepare_set(set_key, rc):
    r_set = []
    for key in rc.smembers(set_key):
        item = {
            'key' : key,
            'type' : rc.type(key),
        }
        r_set.append(item)
    return r_set

def _prepare_hash(hash_key, rc):
    kv_pairs = rc.hgetall(hash_key)
    r_hash = []
    for key in kv_pairs:
        item_type = rc.type(key)
        if 'none' in item_type:
            item_type = rc.type(kv_pairs[key])
        field = {
            'field_name' : key,
            'value' : kv_pairs[key],
            'type' : item_type,
        }
        r_hash.append(field)
    return r_hash

####################
# Helper Functions #
####################
def _form_handler(rc, key, key_type, request):
    if 'list' in key_type:
        if 'back' in request.form['end']:
            rc.lpush(key, request.form['value'])
        else:
            rc.rpush(key, request.form['value'])
    if 'zset' in key_type:
        rc.zadd(key, request.form['score'], request.form['value'])
        return
    if 'set' in key_type:
        rc.sadd(key, request.form['value'])
    if 'hash' in key_type:
        rc.hset(key, request.form['field'], request.form['value'])
    if 'string' in key_type:
        rc.set(key, request.form['value'])


# should be renamed as get redis client
def _get_host_and_port(request):
    env = request.cookies.get('currentEnvironment')
    host = 'localhost'
    port = 6379
    if env:
        host = ENVS['environments'][env]['host']
        port = int(ENVS['environments'][env]['port'])
    return redis.Redis(host, port)

def _get_rdm(request):
    env = request.cookies.get('currentEnvironment')
    host = 'localhost'
    port = 6379
    if env:
        host = ENVS['environments'][env]['host']
        port = int(ENVS['environments'][env]['port'])
    return rdm.RedisDataManager(host=host, port=port)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    app.debug = True
