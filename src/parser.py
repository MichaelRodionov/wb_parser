from typing import Dict, Union, List, Tuple

import requests
from requests import Response


# ----------------------------------------------------------------
class WBParser:
    def __init__(self, address=None, proxy_host=None, proxy_port=None):
        address_data: Dict[str, Dict[str, float]] = {
            'Космодамианская наб., 52с5': {'longitude': 37.643938, 'latitude': 55.732950},
            'Пресненская наб., 10 стр2': {'longitude': 37.535071, 'latitude': 55.747622},
            'default': {'longitude': 37.6201, 'latitude': 55.753737}
        }
        self.longitude: Union[float, str] = address_data.get(address, address_data['default'])['longitude']
        self.latitude: Union[float, str] = address_data.get(address, address_data['default'])['latitude']
        self.address: str = address if address else 'default'

        self.banners_url: str = (
            f'https://banners-website.wildberries.ru/public/v1/banners?'
            f'&longitude={self.longitude}&latitude={self.latitude}'
        )
        self.main_url_params: Dict[str, str] = {
            'urltype': '1024',
            'apptype': '1',
            'displaytype': '3',
            'country': '1',
            'culture': 'ru'
        }
        self.params: Dict[str, str] = {
            'appType': '1',
            'curr': 'rub',
            'dest': '-1257786',
            'page': '1',
            'sort': 'popular',
            'spp': '31'
        }
        self.proxies: Union[Dict[str, str], None] = None

        if proxy_host and proxy_port:
            self.proxy_url: str = f'http://{proxy_host}:{proxy_port}'
            self.proxies: Union[Dict[str, str], None] = {
                'http': self.proxy_url,
                'https': self.proxy_url
            }

    @staticmethod
    def make_request(url, params=None, proxies=None, response=None) -> Union[Response, str]:
        """
        Method to make a request
        """
        request_counter = 1
        while request_counter < 4:
            response = requests.get(url, params=params, proxies=proxies)
            if response.status_code == 200:
                return response
            request_counter += 1
        return f'{response.status_code}'

    def get_banners(self) -> Union[str, List[Dict[str, Union[str, int, List, Dict[str, int]]]]]:
        """
        Method to get response with all banners
        """
        try:
            response = self.make_request(url=self.banners_url, params=self.main_url_params, proxies=self.proxies)
            if isinstance(response, str):
                return response
            elif response.status_code != 200:
                return f'{response.status_code}'
            return response.json()
        except Exception as e:
            return str(e)

    def get_banner_params(self) -> Union[str, List[Dict[str, str]]]:
        """
        Method to get banner params (ID, name, url)
        """
        banners = self.get_banners()
        if not isinstance(banners, str):
            return [
                {
                    'UID': banner['UID'],
                    'name': banner['Alt'],
                    'href': banner['Href']
                } for banner in banners
            ]
        return f'{banners}'

    def promotions_request(self, promotions_data) -> Union[Tuple[str, str], str]:
        """
        Method to get preset and bucket params for promotions products
        """
        url = f'https://static-basket-01.wb.ru/vol0/data{promotions_data["href"].split("?")[0]}-v3.json'
        try:
            response = self.make_request(url=url, proxies=self.proxies)
            if response.status_code != 200:
                return f'{response.status_code}'
            return response.json()['promo']['id'], response.json()['promo']['shardKey'].split('/')[-1]
        except Exception as e:
            return str(e)

    def promotions_products_request(self, banner) -> Union[str, List[str]]:
        """
        Method to get all promotions products
        """
        prom_params = self.promotions_request(banner)
        if not isinstance(prom_params, tuple) or prom_params == 'error':
            return prom_params
        preset, bucket = prom_params[0], prom_params[1]
        url = (
            f'https://search.wb.ru/promo/'
            f'{bucket}/catalog?preset={preset}'
            f'&regions=80,38,83,4,64,33,68,70,30,40,86,75,69,1,31,66,110,48,22,71,114'
        )
        try:
            response = self.make_request(url=url, params=self.params, proxies=self.proxies)
            if response.status_code != 200:
                return f'{response.status_code}'
            return [
                f'https://www.wildberries.ru/catalog/{product["id"]}/detail.aspx'
                for product in response.json()['data']['products']
            ]
        except Exception as e:
            return str(e)

    def brands_request(self, brands_data, fsupplier=None) -> Union[Tuple[str, str], str]:
        """
        Method to get brand and fsupplier params for brands products
        """
        brand = brands_data["href"].split('/')[2]
        url = f'https://static.wbstatic.net/data/brands/{brand}.json'
        if '?' in brand:
            url = f'https://static.wbstatic.net/data/brands/{brand.split("?")[0]}.json'
        try:
            response = self.make_request(url=url, proxies=self.proxies)
            if response.status_code != 200:
                return f'{response.status_code}'
            elif 'fsupplier' in brands_data['href']:
                fsupplier = brands_data['href'].split('fsupplier')[1].split('/')[0].split('&')[0]
            return response.json()['id'], fsupplier
        except Exception as e:
            return str(e)

    def brand_products_request(self, banner) -> Union[str, List[str]]:
        """
        Method to get all brands products
        """
        brand_params = self.brands_request(banner)
        if not isinstance(brand_params, tuple):
            return brand_params
        brand, fsupplier = brand_params[0], brand_params[1]
        url = f'https://catalog.wb.ru/brands/p/catalog?brand={brand}'
        if fsupplier:
            url = f'{url}&fsupplier{fsupplier}'
        try:
            response = self.make_request(url=url, params=self.params, proxies=self.proxies)
            if response.status_code != 200:
                return f'{response.status_code}'
            return [
                f'https://www.wildberries.ru/catalog/{product["id"]}/detail.aspx'
                for product in response.json()['data']['products']
            ]
        except Exception as e:
            return str(e)

    def prepare_response(self, banner, products) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        """
        Method to generate response
        """
        return {
            'platform': 'Wildberries',
            'banner_ID': banner['UID'],
            'ad_product': 'Баннер',
            'ad_place': 'Главная страница',
            'products': products,
            'shop': 'https://www.wildberries.ru',
            'brand': banner['name'],
            'banner_link': f'www.wildberries.ru{banner["href"]}',
            'address': self.address
        }

    def get_result(self) -> Union[List[Dict[str, Union[str, List[Dict[str, str]]]]], str]:
        """
        Method to get result
        """
        products = []
        req_counter = 0
        while req_counter < 10:
            banners = self.get_banner_params()
            if isinstance(banners, str):
                req_counter += 1
            elif not isinstance(banners, str):
                for banner in banners:
                    href_prefix = banner['href'].split('/')[1]
                    if href_prefix == 'promotions':
                        promotion_products = self.promotions_products_request(banner)
                        if not isinstance(promotion_products, str):
                            banner_prom_result = self.prepare_response(banner, promotion_products)
                            if banner_prom_result['products']:
                                products.append(banner_prom_result)
                    elif href_prefix == 'brands':
                        brand_products = self.brand_products_request(banner)
                        if not isinstance(brand_products, str):
                            banner_brand_result = self.prepare_response(banner, brand_products)
                            if banner_brand_result['products']:
                                products.append(banner_brand_result)
                return products
            if req_counter == 10:
                return products


# ----------------------------------------------------------------
if __name__ == '__main__':
    parser = WBParser()
    print(parser.get_result())
