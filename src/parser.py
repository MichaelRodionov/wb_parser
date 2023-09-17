import requests


# ----------------------------------------------------------------
class WBParser:
    def __init__(self, proxy_host=None, proxy_port=None):
        self.url: str = (
            'https://banners-website.wildberries.ru/'
            'public/v1/banners?urltype=1024&apptype=1&displaytype=3'
            '&longitude=37.6201&latitude=55.753737&country=1&culture=ru'
        )
        self.params: dict = {
            'appType': '1',
            'curr': 'rub',
            'dest': '-1257786',
            'page': '1',
            'sort': 'popular',
            'spp': '31'
        }
        self.proxies: dict | None = None

        if proxy_host and proxy_port:
            self.proxy_url: str = f'http://{proxy_host}:{proxy_port}'
            self.proxies = {
                'http': self.proxy_url,
                'https': self.proxy_url
            }

    def get_banners(self) -> list[dict] | str:
        """
        Method to get response with all banners
        """
        try:
            response = requests.get(self.url, proxies=self.proxies)
            if response.status_code != 200:
                return f'{response.status_code}'
            return response.json()
        except Exception as e:
            return str(e)

    def get_banner_params(self) -> list[dict] | str:
        """
        Method to get banner params (ID, name, url)
        """
        banners = self.get_banners()
        if type(banners) != str:
            return [
                {
                    'UID': banner['UID'],
                    'name': banner['Alt'],
                    'href': banner['Href']
                } for banner in banners
            ]
        return f'{banners}'

    def promotions_request(self, promotions_data) -> tuple | str:
        """
        Method to get preset and bucket params for promotions products
        """
        url = f'https://static-basket-01.wb.ru/vol0/data{promotions_data["href"].split("?")[0]}-v3.json'
        try:
            response = requests.get(url, proxies=self.proxies)
            if response.status_code != 200:
                return f'{response.status_code}'
            else:
                return response.json()['promo']['id'], response.json()['promo']['shardKey'].split('/')[-1]
        except Exception as e:
            return str(e)

    def promotions_products_request(self, banner) -> list | str:
        """
        Method to get all promotions products
        """
        preset, bucket = self.promotions_request(banner)
        url = (
            f'https://search.wb.ru/promo/'
            f'{bucket}/catalog?preset={preset}'
            f'&regions=80,38,83,4,64,33,68,70,30,40,86,75,69,1,31,66,110,48,22,71,114'
        )
        try:
            response = requests.get(url, params=self.params, proxies=self.proxies)
            if response.status_code != 200:
                return f'{response.status_code}'
            else:
                return [f'https://www.wildberries.ru/catalog/{product["id"]}/detail.aspx' for product in response.json()['data']['products']]
        except Exception as e:
            return str(e)

    def brands_request(self, brands_data, fsupplier=None) -> tuple | str:
        """
        Method to get brand and fsupplier params for brands products
        """
        brand = brands_data["href"].split('/')[2]
        url = f'https://static.wbstatic.net/data/brands/{brand}.json'
        if '?' in brand:
            url = f'https://static.wbstatic.net/data/brands/{brand.split("?")[0]}.json'
        try:
            response = requests.get(url, proxies=self.proxies)
            if response.status_code != 200:
                return f'{response.status_code}'
            else:
                if 'fsupplier' in brands_data['href']:
                    fsupplier = brands_data['href'].split('fsupplier')[1].split('/')[0].split('&')[0]
                return response.json()['id'], fsupplier
        except Exception as e:
            return str(e)

    def brand_products_request(self, banner) -> list | str:
        """
        Method to get all brands products
        """
        brand, fsupplier = self.brands_request(banner)
        if fsupplier:
            url = f'https://catalog.wb.ru/brands/p/catalog?brand={brand}&fsupplier{fsupplier}'
        else:
            url = f'https://catalog.wb.ru/brands/p/catalog?brand={brand}'
        try:
            response = requests.get(url, params=self.params, proxies=self.proxies)
            if response.status_code != 200:
                return f'{response.status_code}'
            return [f'https://www.wildberries.ru/catalog/{product["id"]}/detail.aspx' for product in response.json()['data']['products']]
        except Exception as e:
            return str(e)

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

    def get_result(self) -> list[dict] | str:
        """
        Method to get result
        """
        products = []
        banners = self.get_banner_params()
        if type(banners) != str:
            for banner in banners:
                if banner['href'].split('/')[1] == 'promotions':
                    promotion_products = self.promotions_products_request(banner)
                    if type(promotion_products) != str:
                        products.append(self.prepare_response(banner, promotion_products))
                    else:
                        return f'Error: {promotion_products}'
                elif banner['href'].split('/')[1] == 'brands':
                    brand_products = self.brand_products_request(banner)
                    if type(brand_products) != str:
                        products.append(self.prepare_response(banner, brand_products))
                    else:
                        return f'Error: {brand_products}'
            return products
        return f'{banners}'


# ----------------------------------------------------------------
if __name__ == '__main__':
    parser = WBParser()
    print(parser.get_result())
