from pyramid.config import Configurator
import redis

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    def add_redis(request):
        db = redis.StrictRedis()
        return db    
    config.add_request_method(add_redis, 'client', reify=True, property=True)    
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('url', '/url')
    config.scan()
    return config.make_wsgi_app()
