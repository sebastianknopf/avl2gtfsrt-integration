class Configuration:

    @classmethod
    def default_config(cls, config: dict) -> dict:
        if 'instances' not in config or not isinstance(config['instances'], list):
            raise RuntimeError('Configuration key "instances" missing or invalid.')
        
        # default configuration at instance level
        default_instance_config: dict = {
            'adapter': {
                'username': None,
                'password': None,
                'interval': 10,
                'autologoff': 1800
            },
            'broker': {
                'port': 1883,
                'username': None,
                'password': None
            }
        }
        
        # run over each instance configured, then verify and enhance it with defaults
        for idx, instance in enumerate(config['instances']):

            # verify instance ID
            if 'id' not in instance:
                cls._raise_invalid_key_exception('id', f"[{idx}]")

            # verify required adapter parameters
            if 'adapter' not in instance:
                cls._raise_invalid_key_exception('adapter', instance['id'])
            
            if 'type' not in instance['adapter']:
                cls._raise_invalid_key_exception('adapter.type', instance['id'])
            
            if 'endpoint' not in instance['adapter']:
                cls._raise_invalid_key_exception('adapter.endpoint', instance['id'])

            if 'interval' in instance['adapter'] and not isinstance(instance['adapter']['interval'], int):
                cls._raise_invalid_key_exception('adapter.interval', instance['id'])

            # verify required broker parameters
            if 'broker' not in instance:
                cls._raise_invalid_key_exception('broker', instance['id'])
            
            if 'host' not in instance['broker']:
                cls._raise_invalid_key_exception('broker.host', instance['id'])
            
            # verify vdv435 parameters
            if 'vdv435' not in instance:
                cls._raise_invalid_key_exception('vdv435', instance['id'])
            
            if 'organisation' not in instance['vdv435']:
                cls._raise_invalid_key_exception('vdv435.organisation', instance['id'])
            
            if 'itcs' not in instance['vdv435']:
                cls._raise_invalid_key_exception('vdv435.itcs', instance['id'])
            
            # merge default configuration per instance afterwards
            config['instances'][idx] = cls._merge_config(default_instance_config, instance)

        return config

    @classmethod
    def _raise_invalid_key_exception(cls, key: str, inst: str) -> None:
        raise RuntimeError(f"Configuration key \"{key}\" missing or invalid in instance \"{inst}\".")

    @classmethod
    def _merge_config(cls, defaults: dict, actual: dict) -> dict:
        if isinstance(defaults, dict) and isinstance(actual, dict):
            return {k: cls._merge_config(defaults.get(k, {}), actual.get(k, {})) for k in set(defaults) | set(actual)}
        
        return actual if actual else defaults