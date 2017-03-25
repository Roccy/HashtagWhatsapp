"""
Hashtag scraper for use on Whatsapp Web

@author: Jamey Sparreboom
"""
import os
import time

from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException,\
        StaleElementReferenceException


CHAT_NAME = "Steen"


def parse_to_date(date):
    """
    Parse date following MM/DD/YYYY
    """
    return datetime.strptime(date, "%m/%d/%Y")


class HashtagWhatsapp(object):
    """
    """

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
                chat_buttons = self.driver.find_elements_by_class_name(
                    "chat-title")
                for chat_button in chat_buttons:
                    if chat_button.text == chat:
                        print("Found %s" % chat)
                        chat_button.click()
                        return
                raise NoSuchElementException()
            except NoSuchElementException, StaleElementReferenceException:
                retries += -1
                time.sleep(timeout)

    def _check_date(self, chat_pane, req_date):
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
                    return True
        except StaleElementReferenceException:
            pass
        return False

    def scroll_back_to_date(self, req_date, retries=5):
        """
        Scroll the chat window back to the point of the requested date
        """
        print("Bloxecuting scroll")
        while retries >= 0:
            try:
                chat_pane = self.driver.find_element_by_class_name(
                    "pane-chat-msgs")
                if not chat_pane.is_selected():
                    chat_pane.click()

                for _ in range(4):
                    chat_pane.send_keys(u'\ue00e')
                    time.sleep(0.05)
                if self._check_date(chat_pane, req_date):
                    return

            except NoSuchElementException, StaleElementReferenceException:
                retries += -1

    def _hashtagged_messages_gen(self, depth=0, retries=5):
        if depth > retries:
            print("Maximum retries reached for retrieving hashtagged messages")
            raise SystemExit()
            
        print("Retrieving Hashtagged Blox")
        try:
            messages = self.driver.find_elements_by_class_name("message-chat")
            for msg in messages:
                # Extract message text
                try:
                    msg_text = msg.find_element_by_class_name("emojitext").text
                except NoSuchElementException:
                    continue

                # Extract message author
                try:
                    msg_author = msg.find_element_by_class_name(
                        "screen-name-text").text
                except NoSuchElementException:
                    msg_author = "Continued msg"

                # Check for hashtags
                if "#" in msg_text:
                    yield msg_text, msg_author
        except StaleElementReferenceException:
            print("References became stale, redoing generation")
            self._hashtagged_messages_gen(depth=depth+1)

    def print_all_hashtagged_messages(self):
        """
        Print all messages available on the screen containing hashtags
        """
        for message, author in self._hashtagged_messages_gen():
            print("\n" + message + "  -" + author)


def main(from_date):
    geckodriver_path = os.path.dirname(os.path.realpath(__file__))
    os.environ["PATH"] += os.pathsep + geckodriver_path

    hw = HashtagWhatsapp()
    hw.wait_for_login()
    hw.select_chat(CHAT_NAME)
    date = parse_to_date(from_date)
    hw.scroll_back_to_date(date)
    hw.print_all_hashtagged_messages()


main("3/1/2017")
