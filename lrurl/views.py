from pyramid.view import view_config
from logging import getLogger
from pyramid.httpexceptions import HTTPBadRequest
import redis
import urlparse
from collections import namedtuple

log = getLogger(__name__)

IndexInfo = namedtuple("IndexInfo", ["key", "value", "identifier"])

@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project': 'LR-Url'}

def index_netloc(url, url_parts):
    yield IndexInfo(key=url_parts.netloc, value=1, identifier=url)

def index_path(url, url_parts):
    for segment in url_parts.path.split('/'):
        yield IndexInfo(key=segment, value=1, identifier=url)

def index_query(url, url_parts):
    for k,vs in urlparse.parse_qs(url_parts.query).iteritems():        
        yield IndexInfo(key=k, value=1, identifier=url)
        for v in vs:
            yield IndexInfo(key=v, value=1, identifier=url)
            yield IndexInfo(key="{0}={1}".format(k,v), value=1, identifier=url)

def get_keys(url, url_parts):
    generators = [index_path, index_query]
    for func in generators:
        for index_tuple in func(url, url_parts):
            yield index_tuple.key

@view_config(route_name="url", renderer="json", request_method="POST")
def get_matches(req):
    url = req.POST.get("url")
    if not url:
        raise HTTPBadRequest("Please Supply a URL")        
    parts = urlparse.urlparse(url)
    keys = {key for key in get_keys(url, parts) if len(key) > 0}
    log.debug(keys)
    req.client.delete("union_result")
    req.client.zunionstore("union_result", keys)
    req.client.delete("final_result")
    req.client.zinterstore("final_result", [parts.netloc, "union_result"])
    results = req.client.zrange("final_result", 0, 9, desc=True, withscores=True)
    data = {"result": []}
    for r in results:
        data['result'].append({"url": r[0], "rank": r[1]})
    return data
