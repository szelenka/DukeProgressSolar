import os
import logging
import datetime
import json
import pandas as pd
from .Selenium import Selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class MyHomeEnergy(Selenium):
    
    def authenticate(self, username: str, password: str, url: str = 'https://duke-energy.myhomeenergy.info/energy_use'):
        # load page
        self.request(url)
        
        # attempt login
        if not self._populate_username(username) or not self._populate_password(password) or not self._click_button('sign_in'):
            raise ValueError('Unable to authenticate')
            
        # verify success
        try:
            usage_elem = WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '//section[@id="overall-use-section"]'))
            )
        except TimeoutException as e:
            self.logger.error('Unable to verify login!')
            return False
        
        return True
    
    def _click_button(self, button_id: str):
        try:
            sign_in = self.driver.find_element_by_xpath('//button[@id="sign_in"]')
            sign_in.click()
        except (NoSuchElementException, AttributeError, ) as e:
            self.logger.warning('Unable to locate {} button'.format(button_id))
            return False
        
        return True
    
    def _populate_username(self, username: str):
        return self._populate_field('user_email', username)
        
    def _populate_password(self, password: str):
        return self._populate_field('user_password', password)
        
    def _populate_field(self, field_id: str, field_value: str):
        try:
            # populate user email address
            field = self.driver.find_element_by_xpath('//input[@id="{}"]'.format(field_id))
            field.clear()
            field.send_keys(field_value)
        except (NoSuchElementException, AttributeError, ValueError, ) as e:
            self.logger.warning('Unable to locate {} field!'.format(field_id))
            return False
        
        return True
    
    def download(self, url: str = 'https://duke-energy.myhomeenergy.info/api/meter_for_year'):
        filename = self.get_download_filename(os.path.basename(url))
        if os.path.isfile(filename):
            return filename
            
        self.request(url)
        try:
            elem = self.driver.find_element_by_tag_name('pre')
        except (NoSuchElementException, ) as e:
            self.logger.error('Unable to locate "pre" tag in: {}'.format(url))
            return None

        try:
            data = json.loads(elem.text)
            json.dump(data, open(filename, 'w'))
        except (json.JSONDecodeError) as e:
            self.logger.error('Unable to load string as JSON!')
            return None
        
        return filename
    
    def load_by_filename(self, filename: str):
        return self.load_by_obj(json.load(open(filename, 'r')))
        
    def load_by_obj(self, json_: dict):
        df = pd.DataFrame(json_.get('samples', {}).get('ELECTRIC', {}).get('ELECTRIC', []))

        drop_columns = ['association_id', 'association_type', 'consumption', 'direction', 'fuelType']
        df = df.drop(drop_columns, axis=1)

        date_columns = ['date', 'rangeEnd', 'rangeStart']
        for col in date_columns:
            df.loc[:,col] = df[col].apply(lambda x: datetime.datetime.strptime(x[:19], '%Y-%m-%dT%H:%M:%S'))

        df['month_int'] = df['date'].apply(lambda x: x.month)
        df['avg_cost_per_kwh'] = df['dollars'].apply(abs) / df['kwh']
        df['days'] = (df['rangeEnd'] - df['rangeStart']).apply(lambda x: x.days)
        df['avg_kwh_per_day'] = df['kwh'] / df['days']
        df['avg_kw_per_hour'] = df['avg_kwh_per_day'] / 24.

        return df.sort_values('date').reset_index(drop=True)
    