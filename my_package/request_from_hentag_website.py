import requests

search_url = 'https://hentag.com/public/api/vault-search'
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6,ja;q=0.5',
    'Dnt': '1',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}


def request_text(search_params: dict, url, request_headers, timeout):
    response = requests.get(url, params=search_params, headers=request_headers, timeout=timeout)
    if response.status_code == 200:
        return response.text


def get_hentag_search_result(search_keywords, timeout_seconds=5, url=search_url, request_headers=None):  # 获取hentag的响应结果
    if request_headers is None:
        request_headers = headers
    try:
        params = {'t': search_keywords}
        original_text = request_text(params, url, request_headers, timeout_seconds)
        return original_text
    except requests.exceptions.RequestException as e:
        #print(f"请求[{url}]失败: {e}")
        return


def get_hentag_metadata(hentag_id,timeout=10,headers=None):
    try:
        metadata_url = rf'https://hentag.com/public/api/vault/{hentag_id}/download?format=hentag&9ab22e521617=420ab7f2c2eb9a784f23'
        res = requests.get(metadata_url, timeout=timeout,headers=headers)
        if res.status_code == 200:
            return res.text
        elif res.status_code == 404:
            return 404
    except requests.exceptions.RequestException as e:
        return
        # print(f'获取metadata失败，{e}')

