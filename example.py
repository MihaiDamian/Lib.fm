from libfm import LibFM
from libfm import LibFMError

# create a handler instance with API key and application secret
lib_fm = LibFM('api key...', 'application secret...')

try:
    lib_fm.create_mobile_session('username...', 'password...')

    # simple read
    info = lib_fm.read('artist.getInfo', artist='Pink Floyd')
    print info['artist']['url']
    for tag in info['artist']['tags']['tag']:
        print tag['name']

    # simple write
    lib_fm.write('artist.addTags', artist='Black Sabbath',
                 tags='metal, classic rock')
except LibFMError, err:
    print err
