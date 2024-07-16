# flickr-to-misskey
Automatically publish photos and locations from Flickr to Misskey

The code uses Misskey's APIs, which you must change to your own:

MISSKEY_API_BASE_URL = 'https://misskey.io'

ACCESS_TOKEN = 'your_misskey_access_token'

The code uses Flickr's APIs, which you have to insert as well:

FLICKR_PUBLIC = ''

FLICKR_SECRET = ''

The code uses OpenCage Geocoder APIs to translate numeric coordinates into human-readable coordinates. Also insert your own:

OPENCAGE_API_KEY = ''
