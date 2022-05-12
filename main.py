import ast
import os
from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


import urllib.parse as urlparse
from urllib.parse import urlencode


timeout = 2
delta = 200


def run():
    url = set_query_params(os.environ['url'])
    driver.get(url)

    login()

    assert_in_legislacoes_page()

    # update all legislacoes from page
    while(True):
        i = 0
        while(True):

            assert_in_legislacoes_page()
            legislacoes = find_elements(
                By.CSS_SELECTOR, '#_com_liferay_journal_web_portlet_JournalPortlet_articlesSearchContainer > div.table-responsive > table > tbody > tr.entry-display-style')

            if (i >= len(legislacoes)):
                break

            update_legislacao(legislacoes[i])

            i += 1
        
        assert_in_legislacoes_page()

        next_page_button = find_element(By.CSS_SELECTOR, '#_com_liferay_journal_web_portlet_JournalPortlet_articlesPageIteratorBottom > ul > li:last-child')
        if not 'disabled' in next_page_button.get_attribute('class'):
            next_page_button.find_element(By.CSS_SELECTOR, 'a.page-link')
            driver.execute_script("arguments[0].click();", next_page_button.find_element(By.CSS_SELECTOR, 'a.page-link'))
        else:
            break


def login():
    if '/web/guest/login' in driver.current_url:
        login = driver.find_element(
            By.ID, '_com_liferay_login_web_portlet_LoginPortlet_login')
        pwd = driver.find_element(
            By.ID, '_com_liferay_login_web_portlet_LoginPortlet_password')
        remember_me = driver.find_element(
            By.ID, '_com_liferay_login_web_portlet_LoginPortlet_rememberMe')

        login.clear()
        login.send_keys(os.environ['email'])
        pwd.clear()
        pwd.send_keys(os.environ['pwd'])

        if not remember_me.is_selected():
            remember_me.click()

        pwd.send_keys(Keys.RETURN)


def update_legislacao(legislacao):
    legislacao_link = legislacao.find_element(
        By.CSS_SELECTOR, 'td:nth-child(2) > a')
    
    # execute script because sometimes this element is behind some 
    # other element making it not clickable
    driver.execute_script("arguments[0].click();", legislacao_link)

    assertInLegislacaoPage()

    int_numero_input = find_element(
        By.CSS_SELECTOR, '[id^="_com_liferay_journal_web_portlet_JournalPortlet_numeroINT_INSTANCE_"]')
    numero_input = find_element(
        By.CSS_SELECTOR, '[id^="_com_liferay_journal_web_portlet_JournalPortlet_numero_INSTANCE_"]')

    int_numero = int_numero_input.get_attribute(
        'value') if int_numero_input.get_attribute('value') else '0'
    numero = numero_input.get_attribute('value')

    go_back_button = find_element(
        By.ID, '_com_liferay_journal_web_portlet_JournalPortlet___com__liferay__journal__web__portlet__JournalPortlet__Menu__voltar')

    if not numero or not numero.isnumeric() or not int(numero) or int(int_numero) == int(numero):
        go_back_button.click()
        return

    # update legislacao
    int_numero_input.clear()
    int_numero_input.send_keys(int(numero))

    # save legislacao
    find_element(
        By.ID, '_com_liferay_journal_web_portlet_JournalPortlet_publishButton').click()

    error_block = find_element(
        By.CSS_SELECTOR, 'div.form-validator-stack.help-block')

    if error_block:
        add_cur_legislacao_to_error_file()
        go_back_button.click()


def add_cur_legislacao_to_error_file():
    file_name = 'legislacoes-not-updated-' + os.environ['env'] + '.txt'

    Path(file_name).touch(exist_ok=True)  # creates file if it doesn't exist
    with open(file_name, 'r') as f:
        names = f.read()

    my_set = set() if not names else ast.literal_eval(names)

    legislacao_name = find_element(
        By.ID, '_com_liferay_journal_web_portlet_JournalPortlet_titleMapAsXML').get_attribute('value')

    my_set.add(legislacao_name)

    with open(file_name, 'w') as f:
        f.write(str(my_set))


def find_element(by, value):
    try:
        element_present = EC.presence_of_element_located((by, value))
        WebDriverWait(driver, timeout).until(element_present)

        try:
            element = driver.find_element(by, value)
            element.text # validate element
            return element
        
        except: # try again
            return driver.find_element(by, value)
    except TimeoutException:
        print("Timed out waiting for page to load")


def find_elements(by, value):
    try:
        element_present = EC.presence_of_element_located((by, value))
        WebDriverWait(driver, timeout).until(element_present)

        return driver.find_elements(by, value)
    except TimeoutException:
        print("Timed out waiting for page to load")


def set_query_params(url):
    params = {'_com_liferay_journal_web_portlet_JournalPortlet_delta': delta,
              '_com_liferay_journal_web_portlet_JournalPortlet_orderByCol': 'title'}

    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)

    url_parts[4] = urlencode(query)

    return urlparse.urlunparse(url_parts)


def assert_in_legislacoes_page():
    title_elem = find_element(
        By.CSS_SELECTOR, '#_com_liferay_journal_web_portlet_JournalPortlet_controlMenu > li.control-menu-nav-category.tools-control-group > ul > li > span')
    assert title_elem.text == "Legislações"


def assertInLegislacaoPage():
    article_structure = find_element(
        By.CSS_SELECTOR, '#basicInformationContent > div > p.article-structure')
    assert article_structure.text == 'Estrutura: Legislações'


driver = webdriver.Chrome()

run()

driver.close()
