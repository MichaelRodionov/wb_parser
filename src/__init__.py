__all__ = ['config']


# ----------------------------------------------------------------
class Config:
    banners_url: str = (
        'https://banners-website.wildberries.ru/'
        'public/v1/banners?urltype=1024&apptype=1&displaytype=3'
        '&longitude=37.6201&latitude=55.753737&country=1&culture=ru'
    )
    static_params: dict = {
        'appType': '1',
        'curr': 'rub',
        'dest': '-1257786',
        'page': '1',
        'sort': 'popular',
        'spp': '31'
    }


# ----------------------------------------------------------------
config: Config = Config()
