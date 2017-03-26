"""
Hashtag scraper for use on Whatsapp Web

@author: Jamey Sparreboom
"""
import os
import time
import argparse

from datetime import datetime
from collections import defaultdict

from dateutil.parser import parse as parse_date
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException,\
        StaleElementReferenceException


DEFAULT_CHAT_NAME = "Steen"


def parse_to_date(date):
    """
    Parse date using dateutil
    """
    return parse_date(date)


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

    def select_chat(self, chat_, retries=5, timeout=2.0):
        """
        Select chat with the given name
        """
        while retries >= 0:
            try:
                chat_buttons = self.driver.find_elements_by_class_name(
                    "chat-title")
                for chat_button in chat_buttons:
                    if chat_button.text == chat_:
                        print("Found %s" % chat)
                        chat_button.click()
                        return
                raise NoSuchElementException()
            except (NoSuchElementException, StaleElementReferenceException):
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

            except (NoSuchElementException, StaleElementReferenceException):
                retries += -1

    def hashtagged_messages_gen(self, retries=5):
        retry_count = 0
        while retry_count <= retries:
            try:
                yield from self._hashtagged_messages_gen()
                break
            except StaleElementReferenceException:
                retry_count += 1

        else:
            print("Maximum retries reached for retrieving hashtagged messages")
            raise SystemExit()

    def _hashtagged_messages_gen(self):
        print("Retrieving Hashtagged Blox")
        try:
            messages = self.driver.find_elements_by_class_name("msg")
            continued_msgs = self.driver.find_elements_by_class_name(
                "msg-continuation")

            tail = []
            for msg in messages:
                try:
                    inner_msg = msg.find_element_by_class_name("message-chat")
                except NoSuchElementException:
                    continue

                if msg in continued_msgs:
                    tail.append(inner_msg)
                    continue

                msg = inner_msg
                if not len(tail):
                    # Extract message text
                    try:
                        msg_text = "%s\n" % msg.find_element_by_class_name(
                            "message-text").text.rstrip()
                    except NoSuchElementException:
                        continue

                    # Extract message author
                    try:
                        msg_author = self._get_author(msg)
                    except NoSuchElementException:
                        msg_author = "Continued msg"

                    # Check for hashtags
                    if "#" in msg_text:
                        yield msg_text, msg_author

                else:
                    tail.append(msg)
                    for msg_text, msg_author in self._cont_message_joining(tail):
                        # Check for hashtags
                        if "#" in msg_text:
                            yield msg_text, msg_author

                tail = []

        except StaleElementReferenceException:
            print("References became stale, redoing generation\n-------------")
            raise

    def find_hashtagged_msgs_grouped(self):
        grouped_by_hashtagee = defaultdict(list)
        for message, author in self.hashtagged_messages_gen():
            hashtagee = self._strip_hashtag(message[message.index("#"):])
            grouped_by_hashtagee[hashtagee].append((message, author))

        for group, messages in grouped_by_hashtagee.items():
            yield "\n\n\n%s:\n" % group
            yield "=====\n"
            for msg, author in messages:
                yield "%s  -%s\n" % (msg, author)

    def _cont_message_joining(self, tail):
        msg_text = ""
        msg_author = ""
        for cont_msg in tail:
            try:
                msg_text = "%s\n%s" % (
                    msg_text,
                    cont_msg.find_element_by_class_name(
                        "message-text").text.rstrip())
            except NoSuchElementException:
                pass

            if msg_author == "":
                msg_author = self._get_author(cont_msg)

            if '#' in msg_text:
                yield "%s\n" % msg_text, msg_author
                msg_text = ""

        yield "%s" % msg_text, msg_author

    def _get_author(self, elem):
        try:
            author_elem = elem.find_element_by_class_name(
                "message-author")
            if "title-number" in author_elem.get_attribute("class"):
                msg_author = author_elem.find_element_by_class_name(
                    "screen-name").text.rstrip()
            else:
                msg_author = author_elem.find_element_by_class_name(
                    "text-clickable").text.rstrip()
        except NoSuchElementException:
            msg_author = ""
            try:
                if "message-out" in elem.get_attribute("class"):
                    msg_author = "Me"
            except NoSuchElementException:
                pass

        return msg_author

    def _strip_hashtag(self, hashtag):
        stripped = "".join(hashtag.split())
        lower_case = stripped.lower()
        proper_case = "".join((lower_case[:2].upper(), lower_case[2:]))
        return proper_case

    def find_all_hashtagged_messages(self):
        """
        Print all messages available on the screen containing hashtags
        """
        for message, author in self.hashtagged_messages_gen():
            yield "\n" + message + "  -" + author

    def print_to_stdout(self, gen):
        for msg in gen:
            print(msg)

    def print_to_file(self, gen, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w+') as f:
            for msg in gen:
                f.write(msg)


def main(from_date, chat=DEFAULT_CHAT_NAME, grouped=False, to_file=None):
    geckodriver_path = os.path.dirname(os.path.realpath(__file__))
    os.environ["PATH"] += os.pathsep + geckodriver_path

    hw = HashtagWhatsapp()
    hw.wait_for_login()
    hw.select_chat(chat)

    date = parse_to_date(from_date)
    hw.scroll_back_to_date(date)

    if grouped:
        msgs_ = hw.find_hashtagged_msgs_grouped()
    else:
        msgs_ = hw.find_all_hashtagged_messages()

    if to_file:
        hw.print_to_file(msgs_, to_file)
    else:
        hw.print_to_stdout(msgs_)


def create_args():
    """
    Set and retrieve commandline arguments using argparse
    """
    parser = argparse.ArgumentParser(description='BLOX!')
    parser.add_argument('from_date', help="date from which messages should be"
                        "loaded in MM\\DD\\YYYY format")
    parser.add_argument('-c', '--chat', help="name of the chat to be scraped")
    parser.add_argument('-g', help="group messages by hashtagee", action='store_true')
    parser.add_argument('-f', '--file', help="write to file")
    return parser.parse_args()


if __name__ == "__main__":
    args = create_args()
    chat = args.chat if args.chat is not None else DEFAULT_CHAT_NAME
    grouped = args.g
    to_file = args.file
    main(args.from_date, chat=chat, grouped=grouped, to_file=to_file)
