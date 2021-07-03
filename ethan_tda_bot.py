from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QTextEdit, QPushButton, QLineEdit, QListWidget
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from robin_stocks import helper as helper
from datetime import datetime, timedelta
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from td.client import TDClient
from td.config import CONSUMER_ID, REDIRECT_URI, ACCOUNT_PASSWORD, ACCOUNT_NUMBER
from pytz import timezone
import requests
import json
import time
import os, sys


def market_order_json(symbol, quantity, direction):
    order = {
        "orderType": "MARKET",
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
            {
                "instruction": direction,
                "quantity": quantity,
                "instrument": {
                    "symbol": symbol,
                    "assetType": "EQUITY"
                }
            }
        ]
    }
    return order


HOST_URL = 'https://ethanherokuwebhookserver.herokuapp.com'
FILE_NAME = 'C://stock_data.csv'

# os.chdir(sys._MEIPASS)
SOURCE_FOLDER = 'res/'
TIMEZONE = 'US/Eastern'

# TradingView Login
Email = "ExecutorEA.alerts@gmail.com"
Password = "Bodhieli29!"
# ChromeDriver Options
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
driver_path = SOURCE_FOLDER + 'chromedriver.exe'


def check_exist_data(file_name, str_data):
    if os.path.isfile(file_name):
        fr = open(file_name, 'r')
        readlines = fr.readlines()
        fr.close()
        for line in readlines:
            if str_data == line[:-1]:
                return True
    return False


def save_data(file_name, str_data):
    fw = open(file_name, 'a')
    fw.write(str_data + '\n')
    fw.close()


def perform_click_chain_by_xpath(driver, click_chain):
    '''
    Safely perform click chain
        Parameters:
            driver (Selenium webdriver): Selenium webdriver
            click_chain (list): list of elements xpath to click
    '''
    for xpath in click_chain:
        if type(xpath) == str:
            try:
                WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                time.sleep(2)
            except:
                try:
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, xpath))).location_once_scrolled_into_view
                    WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                except Exception as e:
                    print(e)
                    return
                else:
                    continue

        elif type(xpath) == list:
            for s_xpath in xpath:
                try:
                    WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, s_xpath))).click()
                    time.sleep(2)
                except:
                    try:
                        WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, s_xpath))).location_once_scrolled_into_view
                        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, s_xpath))).click()
                    except Exception as e:
                        print(e)
                        continue
                    else:
                        continue


def wait(func, t=2):
    def wrapper(*args, **kargs):
        time.sleep(t)
        func(*args, **kargs)

    return wrapper


def back_off(func):
    def wrapper(*args, max_tries=3, sleep_time=2, count=1):
        if count > max_tries:
            return
        try:
            func(*args)
        except Exception as e:
            print(e)
            time.sleep(sleep_time)
            count += 1
            wrapper(sleep_time=2 * count, count=count)
        else:
            return

    return wrapper


class TradeBot(QThread):
    """
    A class to represent a trading bot.

    ...

    Attributes
    ----------
    driver : Selenium webdriver
        Selenium webdriver

    Methods
    -------
    init_driver():
        Create webdriver
    set_alert(ticker, extra_text=''):
        Set alert with name = ticker + extra_text
    """

    def __init__(self, start_time, end_time, parent=None):
        QThread.__init__(self, parent)
        self.driver = None
        self.start_time = start_time
        self.end_time = end_time
        self.current_alert_list = []

    def get_top_symbols(self):
        ticker_list = []
        # Email Button
        screener_page = "https://www.tradingview.com/markets/stocks-usa/market-movers-active/"
        self.driver = webdriver.Chrome(executable_path=driver_path, options=options)
        self.driver.get("https://www.tradingview.com/")
        # Sign in button
        try:
            print(12)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, '/html/body/div[2]/div[3]/div/div[4]/button[1]'))).click()
            print(23)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div[1]'))).click()
            print(34)
            # Enter Email
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     '//*[@id="overlap-manager-root"]/div/div[2]/div/div/div/div/div/div/div[1]/div[4]'))).click()
            print(45)
            # Enter Email
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[contains(@id,"email-signin__user-name-input")]'))).send_keys(
                str(Email))

            # Enter Password
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[contains(@id,"email-signin__password-input")]'))).send_keys(
                str(Password))

            # Sign In
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, '//*[contains(@id, "email-signin__submit")]'))).click()
            time.sleep(3)
            self.driver.get(screener_page)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="js-screener-container"]/div[3]/table/thead/tr/th[3]/div/div/div/div'))).click()
            time.sleep(2)
            for i in range(1, 12):
                ticker_name = self.driver.find_element_by_xpath(
                    f'//*[@id="js-screener-container"]/div[3]/table/tbody/tr[{i}]/td[1]/div/div[2]/a').text
                if ticker_name != 'MTL/P':
                    ticker_list.append(ticker_name)
            time.sleep(1)
            self.driver.close()
        except Exception as e:
            print(e)
        return ticker_list[:10]

    def init_driver(self):
        self.driver = webdriver.Chrome(executable_path=driver_path, options=options)
        self.driver.get("https://www.tradingview.com/")
        print(12)
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[2]/div[3]/div/div[4]/button[1]'))).click()
        print(23)
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div[1]'))).click()
        print(34)
        # Enter Email
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="overlap-manager-root"]/div/div[2]/div/div/div/div/div/div/div[1]/div[4]'))).click()
        print(45)
        # Enter Email
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.XPATH, '//*[contains(@id,"email-signin__user-name-input")]'))).send_keys(
            str(Email))

        # Enter Password
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.XPATH, '//*[contains(@id,"email-signin__password-input")]'))).send_keys(
            str(Password))

        # Sign In
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.XPATH, '//*[contains(@id, "email-signin__submit")]'))).click()
        time.sleep(3)
        self.driver.get('https://www.tradingview.com/chart/5knnvijG/')

    def change_ticker(self, ticker):
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.ID, 'header-toolbar-symbol-search'))).click()
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-role="search"]'))).clear()
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-role="search"]'))).send_keys(ticker)
        time.sleep(3)
        WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div[4]/div/div[1]/div[2]'))).click()

    @wait
    def delete_all_alerts(self):
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[2]/div[5]/div/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div[2]'))).click()
            time.sleep(1)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div[4]/div/div'))).click()
            time.sleep(1)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="overlap-manager-root"]/div/div[2]/div/div/div/div[3]/div[2]/span[2]'))).click()
            time.sleep(1)
        except Exception as e:
            print(e)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[2]/div[5]/div/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div[2]'))).click()
            time.sleep(1)
            print("close alert")

    def edit_alert_info(self, ticker, extra_text):
        # Enter alert name
        alert_input = WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="alert-name"]')))
        alert_input.location_once_scrolled_into_view
        alert_input.send_keys("{} {}".format(ticker, extra_text))

        # Enter alert description
        desc_input = WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[name="description"]')))
        desc_input.location_once_scrolled_into_view
        desc_input.clear()
        desc_input.send_keys("{} {}".format(ticker, extra_text))

        # Click submit
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span.tv-button__loader'))).click()

        # Click ok in warning form
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[name="ok-button"]'))).click()
        except:
            pass

    @wait
    def set_lux_algo_alert(self, ticker, signal_type, extra_text):
        if extra_text == "Buy 1":
            click_chain = [
                '//*[@id="header-toolbar-intervals"]/div[2]',  # select 1m chart
                '//*[@id="header-toolbar-alerts"]',  # alert menu
                '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[1]/span/span[1]/span',
                # condition dropdown
                '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[1]/span/span[2]/span/span/span[6]/span',
                # select Lux Algo
                '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[2]/span/span/span[3]',
                # select type of signal
            ]
        else:
            click_chain = [
                '//*[@id="header-toolbar-intervals"]/div[2]',  # select 1m chart
                '//*[@id="header-toolbar-alerts"]',  # alert menu
                '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[1]/span/span[1]/span',
                # condition dropdown
                '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[1]/span/span[2]/span/span/span[6]/span',
                # select Lux Algo
                '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[2]/span/span/span[3]',
                # select type of signal
            ]
        if signal_type == 'Any Confirmation Sell':
            click_chain.append(
                '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[2]/span/span/span[2]/span/span/span[4]/span')  # any confirmation buy click
        elif signal_type == 'Any Confirmation Buy':
            click_chain.append(
                '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[2]/span/span/span[2]/span/span/span[3]/span')  # any confirmation buy click
        click_chain.append(
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/span[1]/span/span/div[2]/div[1]/div')
        # select once per bar close
        perform_click_chain_by_xpath(self.driver, click_chain)

        desc_input = WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[name="description"]')))
        desc_input.location_once_scrolled_into_view
        desc_input.clear()
        set_text = '{"symbol":"' + ticker + '","direction":"' + extra_text + '"}'
        desc_input.send_keys(set_text)
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[3]/div[2]'))).click()

    @wait
    def set_lux_oscillator_alert(self, ticker, moving_type, percent, extra_text):
        click_chain = [
            '//*[@id="header-toolbar-intervals"]/div[2]',  # select 1m chart
            '//*[@id="header-toolbar-alerts"]',  # alert menu
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[1]/span/span[1]/span',
            # condition dropdown
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[1]/span/span[2]/span/span/span[7]',
            # select Lux Oscillator
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[2]/span/span/span[3]'
            # select type of signal
        ]
        if moving_type == 'Moving Down %':
            click_chain.append(
                '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[2]/span/span/span[2]/span/span/span[20]')
            # select Moving down %
        elif moving_type == 'Moving Up %':
            click_chain.append(
                '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[2]/span/span/span[2]/span/span/span[19]')
            # select Moving up %
        click_chain.append(
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[2]/span/span[3]')
        # select Conf dropdown
        click_chain.append(
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[2]/span/span[2]/span/span/span[20]')
        # select Legacy Main
        click_chain.append(
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/span[1]/span/span/div[2]/div[1]/div')  # select Legacy Main
        # select once per bar close
        perform_click_chain_by_xpath(self.driver, click_chain)
        # Edit moving value
        moving_val_e = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="moving-value"]')))
        moving_val_e.send_keys(Keys.CONTROL + "a")
        moving_val_e.send_keys(Keys.DELETE)
        moving_val_e.send_keys(percent)

        # Edit moving period
        moving_period_e = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="moving-period"]')))
        moving_period_e.send_keys(Keys.CONTROL + "a")
        moving_period_e.send_keys(Keys.DELETE)
        moving_period_e.send_keys("2")

        desc_input = WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[name="description"]')))
        desc_input.location_once_scrolled_into_view
        desc_input.clear()
        set_text = '{"symbol":"' + ticker + '","direction":"' + extra_text + '"}'
        desc_input.send_keys(set_text)
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[3]/div[2]'))).click()

    @wait
    def set_ppsignal_slope(self, ticker, extra_text='Buy 3'):
        click_chain = [
            '//*[@id="header-toolbar-intervals"]/div[2]',  # select 1m chart
            '//*[@id="header-toolbar-alerts"]',  # alert menu
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[1]/span/span[1]/span',
            # condition dropdown
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[1]/span/span[2]/span/span/span[1]',
            # select Heiken Ashi
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[2]/span/span/span[3]',
            # Select Condition Dropdown
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[2]/span/span/span[2]/span/span/span[4]',
            # Select Greater Than
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[3]/span/div[1]/span/span[3]',
            # Select Condition dropdown
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[3]/span/div[1]/span/span[2]/span/span/span[4]',
            # Select PpSignal Slope
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/span[1]/span/span/div[2]/div[1]',
            # select once per bar close
        ]
        perform_click_chain_by_xpath(self.driver, click_chain)

        desc_input = WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[name="description"]')))
        desc_input.location_once_scrolled_into_view
        desc_input.clear()
        set_text = '{"symbol":"' + ticker + '","direction":"' + extra_text + '"}'
        desc_input.send_keys(set_text)
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[3]/div[2]'))).click()

    @wait
    def set_9_ma_alert(self, ticker, extra_text='Sell 2'):
        click_chain = [
            '//*[@id="header-toolbar-intervals"]/div[2]',  # select 1m chart
            '//*[@id="header-toolbar-alerts"]',  # alert menu
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[1]/span/span[1]/span',
            # condition dropdown
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[1]/span/div[1]/span/span[2]/span/span/span[5]/span',
            # select MA 9
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[2]/span/span/span[3]',
            # select type of signal
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/div[2]/span/span/span[2]/span/span/span[12]/span',
            # select Moving up %
            '//*[@id="overlap-manager-root"]/div/div/div[2]/div[1]/div/div/p/form/fieldset/span[1]/span/span/div[2]/div[1]/div',
            # select once per bar close
        ]

        perform_click_chain_by_xpath(self.driver, click_chain)
        # Edit moving value
        moving_val_e = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="moving-value"]')))
        moving_val_e.send_keys(Keys.CONTROL + "a")
        moving_val_e.send_keys(Keys.DELETE)
        moving_val_e.send_keys("0.03")

        # Edit moving period
        moving_period_e = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="moving-period"]')))
        moving_period_e.send_keys(Keys.CONTROL + "a")
        moving_period_e.send_keys(Keys.DELETE)
        moving_period_e.send_keys("2")

        desc_input = WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[name="description"]')))
        # desc_input.location_once_scrolled_into_view
        desc_input.clear()
        set_text = '{"symbol":"' + ticker + '","direction":"' + extra_text + '"}'
        desc_input.send_keys(set_text)
        WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[3]/div[2]'))).click()

        time.sleep(30)

    def close_alerts(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[3]'))).click()
        except:
            pass

    def check_exit_end_of_day(self):
        now = datetime.now()
        print("date now", now)
        end_of_day = (datetime.strptime(self.start_time_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        if now.strftime("%Y-%m-%d %H:%M") >= end_of_day + " 09:30":
            self.init_driver()
            self.delete_all_alerts()
            self.current_alert_list = []
            self.driver.close()
            return True
        return False

    def main_part(self):
        pos_tuple = self.get_top_symbols()
        self.init_driver()
        self.delete_all_alerts()
        for s in pos_tuple:
            try:
                current_time = datetime.now(timezone(TIMEZONE)).strftime("%H:%M")
                if self.start_time > self.end_time:
                    if self.end_time < current_time < self.start_time:
                        return
                else:
                    if self.start_time > current_time or current_time > self.end_time:
                        return
                self.change_ticker(s)
                self.set_lux_algo_alert(s, signal_type='Any Confirmation Buy', extra_text='Buy 1')
                self.set_lux_oscillator_alert(s, 'Moving Up %', '0.03', 'Buy 2')
                self.set_ppsignal_slope(s, 'Buy 3')
                self.set_lux_algo_alert(s, 'Any Confirmation Sell', 'Sell 1')
                self.set_lux_oscillator_alert(s, 'Moving Down %', '0.02', 'Sell 2')
                # self.set_9_ma_alert(s, extra_text='Sell 2')
                time.sleep(1)
            except Exception as e:
                print(e)
                continue
        self.driver.close()

    def run(self):
        print("Starting TradeBot...")
        start_flag = 1
        while True:
            try:
                current_time = datetime.now(timezone(TIMEZONE))
                print(self.start_time, self.end_time, current_time.strftime("%H:%M"))
                if self.start_time > self.end_time:
                    if (current_time.strftime("%H:%M") > self.start_time) or (
                            current_time.strftime("%H:%M") < self.end_time):
                        try:
                            self.main_part()
                            start_flag = 0
                        except Exception as e:
                            print(e)
                    else:
                        if start_flag == 0:
                            try:
                                print("finish day")
                                self.init_driver()
                                self.delete_all_alerts()
                                self.driver.close()
                                start_flag = 1
                            except Exception as e:
                                print(e)
                else:
                    if self.start_time <= current_time.strftime("%H:%M") <= self.end_time:
                        try:
                            self.main_part()
                            start_flag = 0
                        except Exception as e:
                            print(e)
                    else:
                        if start_flag == 0:
                            try:
                                print("finish day")
                                self.init_driver()
                                self.delete_all_alerts()
                                self.driver.close()
                                start_flag = 1
                            except Exception as e:
                                print(e)
            except Exception as e:
                print(e)
            time.sleep(30 * 60)

    def stop(self):
        self.terminate()


class MailCron(QThread):
    def __init__(self, td_session, username, password, start_time, end_time, total_assets, max_positions, parent=None):
        QThread.__init__(self, parent)
        self.td_session = td_session
        self.username = username
        self.password = password
        self.start_time = start_time
        self.end_time = end_time
        self.total_assets = total_assets
        self.max_position = max_positions
        self.current_portfolio = {}
        self.prev_alerts = {}

    def update_current_portfolio(self, ticker, quant, position):
        obj = {
            ticker: {
                'symbol': ticker,
                'quant': quant,
                'position': position,
            }
        }
        if position == 'long':
            if not self.current_portfolio:
                self.current_portfolio = obj
            else:
                self.current_portfolio.update(obj)
        elif position == 'exit':
            self.current_portfolio.pop(ticker, None)

    def order(self, ticker, action, orderType, quant):
        if action == 'BUY':
            my_order = market_order_json(ticker, quant, 'Buy')
            order_status = self.td_session.place_order(account=ACCOUNT_NUMBER, order=my_order)
            print(' \x1b[6;30;42m' + 'Buy' + '\x1b[0m' + ' Triggered on ' + ticker, "qty:", round(quant))
            if "successfully" in order_status:
                print(' \x1b[6;30;42m' + 'Buy' + '\x1b[0m' + ' Triggered on ' + ticker, "qty:", round(quant))
                return True
        elif action == 'SELL':
            my_order = market_order_json(ticker, quant, 'Sell')
            order_status = self.td_session.place_order(account=ACCOUNT_NUMBER, order=my_order)
            print(' \x1b[6;30;41m' + 'Sell' + '\x1b[0m' + ' Triggered on ' + ticker, "qty:", round(quant))
            if "successfully" in order_status:
                print(' \x1b[6;30;41m' + 'Sell' + '\x1b[0m' + ' Triggered on ' + ticker, "qty:", round(quant))
                return True
        return False

    def calculate_lot(self, ticker):
        stock_quote = self.td_session.get_quotes(instruments=[ticker])
        mark_price = float(stock_quote[ticker]['lastPrice'])
        return round(self.total_assets / mark_price)

    def exit_all_orders(self):
        try:
            orders_query = self.td_session.get_orders_query(account=ACCOUNT_NUMBER, status='FILLED')
            for ticker, value in orders_query.items():
                qty = round(float(value['quantity']))
                if qty > 0:
                    my_order = market_order_json(ticker, qty, 'Sell')
                    order_status = self.td_session.place_order(account=ACCOUNT_NUMBER, order=my_order)
                    if "successfully" in order_status:
                        print(' \x1b[6;30;41m' + 'Sell' + '\x1b[0m' + ' Triggered on ' + ticker, "qty:", qty)
            self.current_portfolio.clear()
        except Exception as e:
            print(e)

    def save_alerts(self, signal, ticker, ts):
        if ticker in self.prev_alerts:
            if 'Buy 1' in signal:
                if 'time1' in self.prev_alerts[ticker]:
                    if ts >= self.prev_alerts[ticker]['time1']:
                        self.prev_alerts[ticker]['time1'] = ts
                else:
                    self.prev_alerts[ticker]['time1'] = ts
            if 'Buy 2' in signal:
                if 'time2' in self.prev_alerts[ticker]:
                    if ts >= self.prev_alerts[ticker]['time2']:
                        self.prev_alerts[ticker]['time2'] = ts
                else:
                    self.prev_alerts[ticker]['time2'] = ts
            if 'Buy 3' in signal:
                if 'time3' in self.prev_alerts[ticker]:
                    if ts >= self.prev_alerts[ticker]['time3']:
                        self.prev_alerts[ticker]['time3'] = ts
                else:
                    self.prev_alerts[ticker]['time3'] = ts
        else:
            self.prev_alerts[ticker] = {}
            if 'Buy 1' in signal:
                self.prev_alerts[ticker]['time1'] = ts
            if 'Buy 2' in signal:
                self.prev_alerts[ticker]['time2'] = ts
            if 'Buy 3' in signal:
                self.prev_alerts[ticker]['time3'] = ts

    def check_long_condition(self, total_signals):
        for ticker, content in total_signals.items():
            if 'Buy 1' in content and 'Buy 2' in content and 'Buy 3' in content:
                current_time = datetime.now(timezone(TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")
                save_data("alert_log.txt", current_time + " : " + ticker + " : " + str(content))
                if len(self.current_portfolio) < self.max_position:
                    print("len position", len(self.current_portfolio), "max position", self.max_position)
                    if not ticker in self.current_portfolio:
                        quant = self.calculate_lot(ticker)
                        print("Buying", ticker)
                        # Order
                        order_result = self.order(ticker, action='BUY', orderType='MKT', quant=quant)
                        if order_result:
                            self.update_current_portfolio(ticker, quant, position='long')

    def check_exit_long_condition(self, total_signals):
        for ticker, content in total_signals.items():
            if 'Sell 2' in content or 'Sell 1' in content:
                if len(self.current_portfolio) > 0:
                    if ticker in self.current_portfolio:
                        current_time = datetime.now(timezone(TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")
                        save_data("alert_log.txt", current_time + " : " + ticker + " : " + str(content))
                        quant = abs(float(self.current_portfolio[ticker]['quant']))
                        print("Exiting long", ticker)
                        order_result = self.order(ticker, action='SELL', orderType='MKT', quant=quant)
                        if order_result:
                            self.update_current_portfolio(ticker, quant, position='exit')

    def readmail(self):
        total_buy_signals = {}
        total_sell_signals = {}
        start_time = (datetime.now(timezone(TIMEZONE)) - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
        end_time = datetime.now(timezone(TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")
        sell_start_time = (datetime.now(timezone(TIMEZONE)) - timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S")
        context = {'start_time': start_time, 'end_time': end_time}
        x = requests.post(HOST_URL + '/get_ib_signal/', data=context)
        json_data = json.loads(x.content)
        if json_data['result'] == 'ok':
            payload = json_data['payload']
            for item in payload:
                date_time = item.split(',')[0][9:]
                symbol = item.split(',')[1].split(':')[1]
                signal = item.split(',')[2].split(':')[1]
                if not symbol in total_buy_signals:
                    total_buy_signals[symbol] = []
                    total_buy_signals[symbol].append(signal)
                else:
                    total_buy_signals[symbol].append(signal)
                if sell_start_time <= date_time <= end_time:
                    if not symbol in total_sell_signals:
                        total_sell_signals[symbol] = []
                        total_sell_signals[symbol].append(signal)
                    else:
                        total_sell_signals[symbol].append(signal)
            print("Entering trades")
            self.check_long_condition(total_buy_signals)
            print("Finish checking long condition")
            self.check_exit_long_condition(total_sell_signals)
            print("Finish checking short condition")

    def run(self):
        print("Starting MailCron...")
        start_flag = 1
        while True:
            current_time = datetime.now(timezone(TIMEZONE))
            if self.start_time > self.end_time:
                if (current_time.strftime("%H:%M") > self.start_time) or (
                        current_time.strftime("%H-%M") < self.end_time):
                    print(start_flag)
                    if start_flag == 1:
                        self.td_session.login()
                        self.exit_all_orders()
                    self.readmail()
                    start_flag = 0
                else:
                    if start_flag == 0:
                        print("finish day")
                        self.exit_all_orders()
                        start_flag = 1
            else:
                if self.start_time <= current_time.strftime("%H:%M") <= self.end_time:
                    if start_flag == 1:
                        self.td_session.login()
                        self.exit_all_orders()
                    print('Reading mail')
                    self.readmail()
                    start_flag = 0
                else:
                    if start_flag == 0:
                        print("finish day")
                        self.exit_all_orders()
                        start_flag = 1
            time.sleep(1)

    def stop(self):
        self.terminate()


class MessageBox(QWidget):
    countChanged = pyqtSignal(str)

    def __init__(self, message):
        self.message = message
        super(MessageBox, self).__init__()
        self.setGeometry(850, 600, 320, 222)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.backgroundLabel = QLabel(self)
        self.backgroundLabel.setGeometry(0, 0, 320, 222)
        self.backgroundLabel.setStyleSheet("background-image : url(messagebox.png); background-repeat: no-repeat;")

        self.messageContent = QLabel(self)
        self.messageContent.setText(self.message)
        self.messageContent.setGeometry(34, 82, 280, 40)
        self.messageContent.setStyleSheet("color:white; font-size:16px;")
        self.saveButton = QPushButton(self)
        self.saveButton.setText("Ok")
        self.saveButton.setGeometry(120, 144, 100, 40)
        self.saveButton.clicked.connect(self.OnClose)
        self.saveButton.setStyleSheet("background:#21ce99; border-radius:8px;color:white; font-size:18px; ")
        self.closeBtn = QPushButton(self)
        self.closeBtn.setGeometry(295, 5, 20, 20)
        self.closeBtn.setStyleSheet("background-image : url(close3.png);background-color: transparent; ")
        self.closeBtn.clicked.connect(self.OnClose)

    def OnClose(self):
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)


class SecondWindow(QWidget):
    countChanged = pyqtSignal(str)

    def __init__(self, value, data):
        self.data = data
        super(SecondWindow, self).__init__()
        self.header_text = value
        self.setFixedSize(380, 200)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background:#19181f;")
        self.titleText = QTextEdit(self)
        self.titleText.setText(self.header_text)
        self.titleText.setGeometry(20, 30, 340, 60)
        self.titleText.setStyleSheet("color:white; font-size:16px;border:none;")
        self.RequestCodeEdit = QLineEdit(self)
        self.RequestCodeEdit.setStyleSheet("background:#24202a; color:white; font-size:16px;")
        self.RequestCodeEdit.setGeometry(20, 70, 340, 30)
        self.confirmButton = QPushButton(self)
        self.confirmButton.setText("Confirm")
        self.confirmButton.setGeometry(110, 130, 160, 40)
        self.confirmButton.clicked.connect(self.OnShow)
        self.confirmButton.setStyleSheet("background:#21ce99; border-radius:8px;color:white; font-size:16px;")
        print(self.data)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)


class MainWindow(QWidget):
    start_flag = 1

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setGeometry(250, 50, 716, 458)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Robinhood Bot Panel")
        self.username = "e.paulson95@hotmail.com"
        self.password = "ExecutorEA2021$"
        self.backgroundLabel = QLabel(self)
        self.backgroundLabel.setGeometry(0, 0, 716, 458)
        self.backgroundLabel.setStyleSheet(
            "background-image : url(" + SOURCE_FOLDER + "Robinhood_bot2.png); background-repeat: no-repeat;")
        font = QFont()
        font.setPointSize(20)
        self.closeBtn = QPushButton(self)
        self.closeBtn.setGeometry(680, 10, 29, 29)
        self.closeBtn.setStyleSheet(
            "background-image : url(" + SOURCE_FOLDER + "close2.png);background-color: transparent;")
        self.closeBtn.clicked.connect(self.onClose)

        self.startBtn = QPushButton(self)
        self.startBtn.setGeometry(444, 18, 216, 60)
        self.startBtn.setText("Start")
        self.startBtn.setStyleSheet("background-color: #21ce99; border-radius: 18px; color:white; font-size:24px;")
        self.startBtn.clicked.connect(self.onStart)

        self.usernameEdit = QLineEdit(self)
        self.usernameEdit.setStyleSheet(
            "background-color: transparent; border-radius: 15px; color:white; font-size:16px;")
        self.usernameEdit.setGeometry(144, 117, 180, 24)
        self.usernameEdit.setText(self.username)
        self.visibleIcon = QIcon(SOURCE_FOLDER + "eye.svg")
        self.hiddenIcon = QIcon(SOURCE_FOLDER + "hidden.svg")
        self.passwordEdit = QLineEdit(self)
        self.passwordEdit.setStyleSheet(
            "background-color: transparent; border-radius: 15px; color:white; font-size:16px;")
        self.passwordEdit.setGeometry(519, 117, 159, 24)
        self.passwordEdit.setText(self.password)
        self.passwordEdit.setEchoMode(QLineEdit.Password)
        self.passwordEdit.togglepasswordAction = self.passwordEdit.addAction(
            self.visibleIcon,
            QLineEdit.TrailingPosition
        )
        # self.password.setText(robin_pass)
        self.password_shown = False
        self.passwordEdit.togglepasswordAction.triggered.connect(self.on_toggle_password_Action)

        self.totalAssetsLabel = QLabel(self)
        self.totalAssetsLabel.setStyleSheet(
            "background-color: transparent; border-radius: 6px; color:white; font-size:18px;")
        self.totalAssetsLabel.setGeometry(20, 240, 120, 30)
        self.totalAssetsLabel.setText("Total Assets:")
        self.totalAssetsLabel.setAlignment(Qt.AlignRight)
        self.totalAssetsEdit = QLineEdit(self)
        self.totalAssetsEdit.setStyleSheet(
            "background-color: #343438; border-radius: 6px; color:white; font-size:18px;")
        self.totalAssetsEdit.setGeometry(150, 240, 130, 30)
        self.totalAssetsEdit.setText("5000")
        self.totalAssetsEdit.setAlignment(Qt.AlignCenter)

        self.maxPositionLabel = QLabel(self)
        self.maxPositionLabel.setStyleSheet(
            "background-color: transparent; border-radius: 6px; color:white; font-size:18px;")
        self.maxPositionLabel.setGeometry(20, 285, 120, 30)
        self.maxPositionLabel.setText("Max Positions:")
        self.maxPositionLabel.setAlignment(Qt.AlignRight)
        self.maxPositionEdit = QLineEdit(self)
        self.maxPositionEdit.setStyleSheet(
            "background-color: #343438; border-radius: 6px; color:white; font-size:18px;")
        self.maxPositionEdit.setGeometry(150, 285, 130, 30)
        self.maxPositionEdit.setText("5")
        self.maxPositionEdit.setAlignment(Qt.AlignCenter)

        self.trailingStopPercentLabel = QLabel(self)
        self.trailingStopPercentLabel.setStyleSheet(
            "background-color: transparent; border-radius: 6px; color:white; font-size:18px;")
        self.trailingStopPercentLabel.setGeometry(20, 330, 120, 30)
        self.trailingStopPercentLabel.setText("Trail Stop(%):")
        self.trailingStopPercentLabel.setAlignment(Qt.AlignRight)
        self.trailingStopPercentEdit = QLineEdit(self)
        self.trailingStopPercentEdit.setStyleSheet(
            "background-color: #343438; border-radius: 6px; color:white; font-size:18px;")
        self.trailingStopPercentEdit.setGeometry(150, 330, 130, 30)
        self.trailingStopPercentEdit.setText("5")
        self.trailingStopPercentEdit.setAlignment(Qt.AlignCenter)

        self.startTimeLabel = QLabel(self)
        self.startTimeLabel.setStyleSheet(
            "background-color: transparent; border-radius: 6px; color:white; font-size:18px;")
        self.startTimeLabel.setGeometry(420, 240, 170, 30)
        self.startTimeLabel.setText("Start Time:")
        self.startTimeLabel.setAlignment(Qt.AlignCenter)
        self.startTimeEdit = QLineEdit(self)
        self.startTimeEdit.setStyleSheet(
            "background-color: #343438; border-radius: 6px; color:white; font-size:18px;")
        self.startTimeEdit.setGeometry(560, 240, 130, 30)
        self.startTimeEdit.setText("09:00")
        self.startTimeEdit.setAlignment(Qt.AlignCenter)

        self.endTimeLabel = QLabel(self)
        self.endTimeLabel.setStyleSheet(
            "background-color: transparent; border-radius: 6px; color:white; font-size:18px;")
        self.endTimeLabel.setGeometry(420, 285, 170, 30)
        self.endTimeLabel.setText("Edit Time:")
        self.endTimeLabel.setAlignment(Qt.AlignCenter)
        self.endTimeEdit = QLineEdit(self)
        self.endTimeEdit.setStyleSheet(
            "background-color: #343438; border-radius: 6px; color:white; font-size:18px;")
        self.endTimeEdit.setGeometry(560, 285, 130, 30)
        self.endTimeEdit.setText("15:40")
        self.endTimeEdit.setAlignment(Qt.AlignCenter)

    def on_toggle_password_Action(self):
        if not self.password_shown:
            self.passwordEdit.setEchoMode(QLineEdit.Normal)
            self.password_shown = True
            self.passwordEdit.togglepasswordAction.setIcon(self.hiddenIcon)
        else:
            self.passwordEdit.setEchoMode(QLineEdit.Password)
            self.password_shown = False
            self.passwordEdit.togglepasswordAction.setIcon(self.visibleIcon)

    def onStart(self):
        global account_type
        if self.start_flag == 1:
            self.username = self.usernameEdit.text()
            self.password = self.passwordEdit.text()
            if self.username != '' and self.password != '':
                try:
                    self.td_session = TDClient(account_number=ACCOUNT_NUMBER,
                                               account_password=ACCOUNT_PASSWORD,
                                               consumer_id=CONSUMER_ID,
                                               redirect_uri=REDIRECT_URI)
                    if self.td_session.login():
                        self.startBtn.setText("Stop")
                        self.bot = TradeBot(self.startTimeEdit.text(),
                                            self.endTimeEdit.text())
                        self.mail_bot = MailCron(self.td_session,
                                                 self.username,
                                                 self.startTimeEdit.text(),
                                                 self.endTimeEdit.text(),
                                                 float(self.totalAssetsEdit.text()),
                                                 int(self.maxPositionEdit.text()))
                        self.bot.start()
                        self.mail_bot.start()
                        self.start_flag = 0
                    else:
                        self.TW = MessageBox("Login Failed Try again!")
                        self.TW.show()
                except Exception as e:
                    print(e)
            else:
                try:
                    if self.username == '':
                        self.TW = MessageBox("Please enter your email!")
                        self.TW.show()
                    else:
                        self.TW = MessageBox("Please enter your Password!")
                        self.TW.show()
                except Exception as e:
                    print(e)
        else:
            self.startBtn.setText("Start")
            self.start_flag = 1
            self.bot.stop()
            # self.mail_bot.stop()

    def onClose(self):
        try:
            global app
            if self.start_flag == 0:
                self.start_flag = 1
                self.bot.stop()
                self.mail_bot.stop()
            app.quit()
        except Exception as e:
            print(e)

    def OrderUpdate(self, value):
        print(value)
        if value == 'success':
            self.startBtn.setText("Stop")
            self.bot = TradeBot(self.startTimeEdit.text(),
                                self.endTimeEdit.text())
            self.mail_bot = MailCron(self.td_session,
                                     self.startTimeEdit.text(),
                                     self.endTimeEdit.text(),
                                     float(self.totalAssetsEdit.text()),
                                     int(self.maxPositionEdit.text()))
            self.bot.start()
            self.mail_bot.start()
            self.start_flag = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)

    def onProcess(self, perfomance):
        self.listwidget.addItem(perfomance)


if __name__ == '__main__':
    import sys

    global app
    app = QApplication(sys.argv)
    MW = MainWindow()
    MW.show()
    sys.exit(app.exec_())
