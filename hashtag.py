"""
Hashtag scraper for use on Whatsapp Web

@author: Jamey Sparreboom
"""
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException,\
        StaleElementReferenceException
from datetime import datetime

import time

CHAT_NAME = "Steen"

def parse_to_date(date):
    return datetime.strptime(date, "%m/%d/%Y")   

class HashtagWhatsapp(object):

    URL = "https://web.whatsapp.com/"
    WAIT_FOR_LOGIN_REFRESH_RATE = 2.0

    def __init__(self):
        driver = webdriver.Firefox()
        driver.get(self.URL)
        self.driver = driver

    def wait_for_login(self):
        """
        Wait for the login screen with the QR-code
        """
        print("Waiting to pass login screen")
        while True:
            try:
                time.sleep(self.WAIT_FOR_LOGIN_REFRESH_RATE)
                self.driver.find_element_by_class_name("entry-main")
            except NoSuchElementException:
                time.sleep(self.WAIT_FOR_LOGIN_REFRESH_RATE)
                break

    def select_chat(self, chat, retries=5, timeout=2.0):
        """
        Select chat with the given name
        """
        while retries >= 0:
            try:
                chat_buttons = self.driver.find_elements_by_class_name("chat-title")
                for chat_button in chat_buttons:
                    if chat_button.text == chat:
                        print("Found %s" % chat)
                        chat_button.click()
                        return
                raise NoSuchElementException()
            except NoSuchElementException:
                retries += -1
                time.sleep(timeout)

    def scroll_back_to_date(self, req_date, retries=5):
        print("Bloxecuting scroll")
        while retries >= 0:
            try:
                chat_pane = self.driver.find_element_by_class_name("pane-chat-msgs")
                chat_pane.click()
                if chat_pane.is_selected:
                    for _ in range(4):
                        chat_pane.send_keys(u'\ue00e')
                        time.sleep(0.05)
                    # self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    system_msgs = chat_pane.find_elements_by_class_name("message-system")
                    try:
                        for sysmsg in system_msgs:
                            inner_elem = sysmsg.find_element_by_class_name("emojitext")
                            date = inner_elem.text
                            if len(date.split("/")) != 3:
                                continue
                            found_date = datetime.strptime(date, "%m/%d/%Y")   
                            if found_date < req_date:
                                print("Bloxxed back enough")
                                return

                    except StaleElementReferenceException:
                        pass
            except NoSuchElementException:
                retries += -1

    def _hashtagged_messages_gen(self):
        print("Retrieving Hashtagged Blox")
        messages = self.driver.find_elements_by_class_name("message-chat")
        for msg in messages:
            # Extract message text
            try:
                msg_text = msg.find_element_by_class_name("emojitext").text
            except NoSuchElementException:
                continue

            # Extract message author
            try:
                msg_author = msg.find_element_by_class_name("screen-name-text").text
            except NoSuchElementException:
                msg_author = "Continued msg"

            # Check for hashtags 
            if "#" in msg_text:
                yield msg_text, msg_author

    def print_all_hashtagged_messages(self):
        for message, author in self._hashtagged_messages_gen():
            print(message + "  -" + author)


def main(from_date):
    hw = HashtagWhatsapp()
    hw.wait_for_login()
    hw.select_chat(CHAT_NAME)
    date = parse_to_date(from_date)
    hw.scroll_back_to_date(date)
    hw.print_all_hashtagged_messages()

main("1/1/2017")
