# flickr-to-misskey
Automatically publish photos and locations from Flickr to Misskey

The publication will look like this:

![Screenshot_1](https://github.com/user-attachments/assets/3448391a-5679-4ce4-97ac-0f9b85609768)

# Перед запуском проверь:

Установлены ли библиотеки

```
pip install misskey
```


The code uses Misskey's APIs, which you must change to your own:

MISSKEY_API_BASE_URL = ''

ACCESS_TOKEN = ''

The code uses Flickr's APIs, which you have to insert as well:

FLICKR_PUBLIC = ''

FLICKR_SECRET = ''

The code uses OpenCage Geocoder APIs to translate numeric coordinates into human-readable coordinates. Also insert your own:

OPENCAGE_API_KEY = ''
