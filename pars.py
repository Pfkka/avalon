import re
import requests
import datetime
from config import url
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


class Parser:
    def __init__(self):
        self.driver = webdriver.PhantomJS()
        self.driver.wait = WebDriverWait(self.driver, 5)
        self.driver.get(url)
        self.weeks = {"предыдущая": "Previous", "текущая": "Current", "следующая": "Next"}
        self.start_time = datetime.datetime.now()

    def parsing(self, group_value, week):
        now = datetime.datetime.now()
        if now - self.start_time > datetime.timedelta(minutes=10):
            self.driver.get(url)
            self.start_time = now
        box = Select(self.driver.wait.until(EC.presence_of_element_located(
            (By.ID, "MainContent_ColumnsContent_MiddleContent_ddlPrograms"))))
        box.select_by_value(group_value)

        elem = self.driver.find_element_by_id(
            "MainContent_ColumnsContent_MiddleContent_btn" + self.weeks[week])  # _btnCurrent  or _btnNext...
        if week != "текущая":
            elem.click()

        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        main_table = soup.find("table",
                               id="MainContent_ColumnsContent_MiddleContent_ctrlWeekScheduleGridView_gvWeekSchedule")
        dates = main_table.find_all("span", {"data-format": "{0}<br />{1:d}"})
        content_table = main_table.find_all("table", {"border": "1"})

        data = {}
        for i in range(len(dates)):
            content = {}
            mess = content_table[i].find("div", {"class": "alert alert-warning mb-0"})
            if mess:
                data[dates[i].get_text(separator=" ")] = mess.text.replace("\n", "")
            else:
                head = content_table[i].find_all("th", {"scope": "col"})
                body = content_table[i].find_all("td")
                first_col = body[0].find_all("a")
                content[head[0].text] = [k.text for k in first_col]
                for j in range(1, len(head)):
                    content[head[j].text] = body[j].text.replace("\n", "")
                data[dates[i].get_text(separator=" ")] = content

        return data

    @staticmethod
    def check_user_input(user_input, groups):

        value = user_input.lower().split(" ")
        result = []
        for i in groups:
            flag = False
            words = re.findall(r"\w+", i.replace("-", " ").lower())
            k = 0
            for user_word in value:
                for word in words:
                    if user_word == word:
                        k += 1
                        break
                if k == len(value):
                    flag = True
                    break
            if flag:
                result.append(i)
        return result

    @staticmethod
    def get_groups():
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")
        result = soup.findAll("option")

        dbase = {}
        for i in result[1:]:
            dbase[i.text] = i.attrs["value"]

        return dbase
