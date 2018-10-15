import os
import logging
import time
import json
import pandas as pd
from .Selenium import Selenium
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class PVWatts(Selenium):
    street_address = None
    
    def __init__(self, street_address: str):
        super(PVWatts, self).__init__()
        self.street_address = street_address
    
    def setup(self):
        options = webdriver.ChromeOptions() 
        options.add_experimental_option("prefs", {
            "download.default_directory": self.download_directory
        })
        self.driver = webdriver.Chrome(self.driver_path, options=options)
    
    def download(self, url: str = 'https://pvwatts.nrel.gov/pvwatts.php'):
        filename = self.get_download_filename('pvwatts_monthly', 'csv')
        if os.path.isfile(filename):
            return filename
            
        self.request(url)
        # populate address
        try:
            address = self.driver.find_element_by_xpath('//*[@id="myloc2"]')
            address.send_keys(self.street_address)

            # submit address
            submit = self.driver.find_element_by_xpath('//*[@id="go2"]')
            submit.click()
        except NoSuchElementException as e:
            pass

        # wait for it to resolve
        resolved = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="datasettext"]/div/span[text()[contains(., "Lat, Lon")]]'))
        )

        # pre-populate default solar system  
        info = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="snsysteminfo"]'))
        )
        info.click()
        
        # populate the kWh of the proposed system
        kwh = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="system_capacity"]'))
        )
        kwh.clear()
        kwh.send_keys('10')

        # select array type for roof
        array_type = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="array_type"]/option[@value[contains(., "Fixed (roof mount)")]]'))
        )
        array_type.click()
        
        # navigate to results page
        results = self.driver.find_element_by_xpath('//*[@id="snresults"]')
        results.click()

        monthly = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="exportresults"]/a[text()[contains(., "Monthly")]]'))
        )
        
        old_files = set(os.listdir(self.download_directory))
        
        # the site is weird, we need to trigger the click from JavaScript
        self.driver.execute_script("""
        var elem = document.getElementById('exportresults'),
            target = null;
        if (elem && elem.children.length > 0) {
            target = [].slice.call(elem.children).filter(x => x.innerHTML == 'Monthly');
            target[0].click();
        }
        """)
            
        # get filename it just downloaded
        tmp_filename = self.get_temp_download_filename(old_files)
        self.logger.info('Waiting for download to complete...,')
        while (tmp_filename.endswith('.crdownload')):
            time.sleep(1)
            tmp_filename = self.get_temp_download_filename(old_files)
            print(tmp_filename)
        self.logger.info('Moving filename: {} -> {}'.format(tmp_filename, filename))
        os.rename(tmp_filename, filename)
        return filename
    
    def get_temp_download_filename(self, old_files):
        new_files = set(os.listdir(self.download_directory))
        tmp_filename = os.path.abspath(os.path.join(self.download_directory, new_files.difference(old_files).pop()))
        return tmp_filename
        
    def load_by_filename(self, filename: str):
        df = pd.read_csv(filename, header=16)
        df['Month'] = pd.to_numeric(df['Month'], errors='coerce').dropna()
        df = df[['Month', 'Solar Radiation (kWh/m^2/day)']].rename({
            'Month': 'month_int',
            'Solar Radiation (kWh/m^2/day)': 'radiation_hours_per_day'
        }, axis='columns')

        return df
    