import requests

from src import config


# ----------------------------------------------------------------
class WBParser:
    def __init__(self, proxy_host=None, proxy_port=None):
        self.url: str = config.banners_url
        self.params: dict = config.static_params
        self.proxies = None

        if proxy_host and proxy_port:
            self.proxy_url: str = f'http://{proxy_host}:{proxy_port}'
            self.proxies = {
                'http': self.proxy_url,
                'https': self.proxy_url
            }

    def get_banners(self) -> list[dict]:
        """
        Method to get response with all banners
        """
        return requests.get(self.url, proxies=self.proxies).json()

    def get_banner_params(self) -> list[dict]:
        """
        Method to get banner params (ID, name, url)
        """
        return [
            {
                'UID': banner['UID'],
                'name': banner['Alt'],
                'href': banner['Href']
            } for banner in self.get_banners()
        ]

    def promotions_request(self, promotions_data) -> tuple:
        """
        Method to get preset and bucket params for promotions products
        """
        url = f'https://static-basket-01.wb.ru/vol0/data{promotions_data["href"].split("?")[0]}-v3.json'
        response = requests.get(url, proxies=self.proxies).json()
        return response['promo']['id'], response['promo']['shardKey'].split('/')[-1]

    def promotions_products_request(self, banner) -> list:
        """
        Method to get all promotions products
        """
        preset, bucket = self.promotions_request(banner)
        url = (
            f'https://search.wb.ru/promo/'
            f'{bucket}/catalog?preset={preset}'
            f'&regions=80,38,83,4,64,33,68,70,30,40,86,75,69,1,31,66,110,48,22,71,114'
        )
        response = requests.get(url, params=self.params, proxies=self.proxies).json()
        return response['data']['products']

    def brands_request(self, brands_data, fsupplier=None) -> tuple:
        """
        Method to get brand and fsupplier params for brands products
        """
        brand = brands_data["href"].split('/')[2]
        url = f'https://static.wbstatic.net/data/brands/{brand}.json'
        if '?' in brand:
            url = f'https://static.wbstatic.net/data/brands/{brand.split("?")[0]}.json'
        response = requests.get(url, proxies=self.proxies).json()
        if 'fsupplier' in brands_data['href']:
            fsupplier = brands_data['href'].split('fsupplier')[1].split('/')[0].split('&')[0]
        return response['id'], fsupplier

    def brand_products_request(self, banner) -> list:
        """
        Method to get all brands products
        """
        brand, fsupplier = self.brands_request(banner)
        if fsupplier:
            url = f'https://catalog.wb.ru/brands/p/catalog?brand={brand}&fsupplier{fsupplier}'
        else:
            url = f'https://catalog.wb.ru/brands/p/catalog?brand={brand}'
        response = requests.get(url, params=self.params, proxies=self.proxies).json()
        return response['data']['products']

    @staticmethod
    def prepare_response(banner, products) -> dict:
        """
        Method to generate response
        """
        return {
            'Площадка': 'Wildberries',
            'ID баннера': banner['UID'],
            'Название рекламного продукта': 'Баннер',
            'Расположение на странице': 'Главная страница',
            'SKU': products,
            'Магазин': 'www.wildberries.ru',
            'Бренд': banner['name'],
            'Ссылка на креатив': f'www.wildberries.ru{banner["href"]}'
        }

    def get_result(self):
        """
        Method to get result
        """
        products = []
        for banner in self.get_banner_params():
            if banner['href'].split('/')[1] == 'promotions':
                products.append(self.prepare_response(banner, self.promotions_products_request(banner)))
            elif banner['href'].split('/')[1] == 'brands':
                products.append(self.prepare_response(banner, self.brand_products_request(banner)))
        return products


# ----------------------------------------------------------------
if __name__ == '__main__':
    parser = WBParser()
    print(parser.get_result())
