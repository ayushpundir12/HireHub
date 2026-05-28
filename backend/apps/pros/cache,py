from django.core.cache import cache
import hashlib, json

DISCOVERY_TTL  = 300   # 5 min
PROFILE_TTL    = 120   # 2 min


def discovery_cache_key(params: dict) -> str:
    stable = json.dumps(params, sort_keys=True)
    return 'pros:' + hashlib.md5(stable.encode()).hexdigest()


def profile_cache_key(pro_id) -> str:
    return f'pro:{pro_id}'


def invalidate_pro_cache(pro_id):
    """Call this whenever a ProProfile is updated."""
    cache.delete(profile_cache_key(pro_id))