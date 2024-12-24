from requests import request
from rest_framework.utils import json

url = 'http://apis.data.go.kr/B552584/MsrstnInfoInqireSvc/getMsrstnList'
service_key = 'A+qrwdK3yRSOh3BGF7noYwimDaU1FKCGWxky5WFKPTbs8OG2/FHbgjVg+wXyu41fySFpD9a93E5bxivM3mDn4w=='
params = {
    'serviceKey': service_key,
    'returnType': 'json',
    'numOfRows': 1000,
}

region_data = request('get', url, params=params).json()
region_data = region_data['response']['body']['items']
area = []
for address in region_data:
    tmp = address['addr'].split(' ')
    area.append(f'{tmp[0][:2]} {address['stationName']}')
area = set(area)
result = {}
for aaa in area:
    si = aaa.split(' ')[0]
    goon = aaa.split(' ')[1]
    if si not in result:
        result[si] = []
    result[si].append(goon)
with open('addr.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(result, indent=4, ensure_ascii=False))

