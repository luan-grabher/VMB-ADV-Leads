

import os
import zipfile

import requests


chromedriver_path = './chromedriver.exe'
api_get_download_chromedriver = 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json'
platform = 'win32'
folder_inside_zip = 'chromedriver-win32'

def install_chromedriver(force=False):
    isChromedriverExists = os.path.isfile(chromedriver_path)
    if isChromedriverExists and not force:
        print('chromedriver already installed')
        return
    
    print('installing chromedriver')

    response = requests.get(api_get_download_chromedriver)
    response.raise_for_status()
    json = response.json()

    chrome_driver_urls = json['channels']['Stable']['downloads']['chromedriver']
    download_url = None
    for chrome_driver_url in chrome_driver_urls:
        if chrome_driver_url['platform'] == platform:
            download_url = chrome_driver_url['url']
            break
    
    if not download_url:
        raise Exception('download_url not found')
    
    response = requests.get(download_url)
    response.raise_for_status()

    with open('chromedriver.zip', 'wb') as file:
        file.write(response.content)

    
    with zipfile.ZipFile('chromedriver.zip', 'r') as zip_ref:
        zip_ref.extractall('.')

    os.remove('chromedriver.zip')
    os.rename(folder_inside_zip + '/chromedriver.exe', chromedriver_path)
    
    for file in os.listdir(folder_inside_zip):
        os.remove(folder_inside_zip + '/' + file)
    os.rmdir(folder_inside_zip)

    print('chromedriver installed with version: ', json['channels']['Stable']['version'])



if __name__ == '__main__':
    install_chromedriver()
