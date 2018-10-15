import os
import logging
import datetime
from selenium import webdriver
import selenium.webdriver.chrome.service as service
from selenium.common.exceptions import NoSuchElementException


class Selenium(object):
    logger = None
    driver = None
    data_directory = None
    download_directory = None
    driver_path = None
    
    def __init__(self, data_directory: str = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_directory = os.path.abspath(os.path.join(os.path.basename(__file__), '../data') or data_directory)
        self.setup_downloads()
        self.driver_path = os.path.abspath(os.path.join(os.path.basename(__file__), '../drivers/chromedriver'))
        self.logger.info('Using driver: {}'.format(self.driver_path))
        self.logger.info('Downloading to: {}'.format(self.download_directory))
        self.setup()
        
    def __del__(self):
        self.tearDown()
        
    def setup_downloads(self):
        self.download_directory = os.path.abspath(os.path.join(os.path.basename(__file__), self.data_directory, './raw'))

        # verify the directory exists
        try:
            os.makedirs(self.download_directory)
        except FileExistsError:
            pass
        
        # purge any old files
#         for filename in map(lambda x: os.path.join(self.download_directory, x), os.listdir(self.download_directory)):
#             self.logger.warning('Deleting file: {}'.format(filename))
#             os.unlink(filename)
        
    def setup(self):
        svc = service.Service(self.driver_path)
        svc.start()
        options = webdriver.ChromeOptions()
        options.add_experimental_option('prefs', {
            'download.default_directory': self.download_directory
        })
        self.driver = webdriver.Remote(svc.service_url)
        
    def tearDown(self):
        if self.driver:
            self.driver.quit()
        
    def request(self, url: str, method: str = 'GET'):
        return self.driver.get(url)
    
    def xpath(self, xpath: str):
        try:
            return self.driver.find_element_by_xpath(xpath)
        except NoSuchElementException as e:
            pass
        
        return None
    
    def download(self, url: str):
        raise NotImplementedError('download must be implemented by child class!')
    
    def get_download_filename(self, prefix, extension='json'):
        return os.path.abspath(os.path.join(self.download_directory, './{prefix}_{date}.{extension}'.format(
            prefix=prefix,
            date=datetime.datetime.utcnow().strftime('%Y%m%d'),
            extension=extension
        )))
    
    def load_by_filename(self, filename: str):
        raise NotImplementedError('load_by_filenamej must be implemented by child class!')
        
    def load_by_obj(self, _json: dict):
        raise NotImplementedError('load_by_obj must be implemented by child class!')
    
    def to_dataframe(self, filename: str = None):
        df = self.load_by_filename(filename or self.download())
        filename = os.path.abspath(os.path.join(self.data_directory, './interm/{prefix}.csv'.format(
            prefix=self.__class__.__name__
        )))
        df.to_csv(filename, index=False)
        return df