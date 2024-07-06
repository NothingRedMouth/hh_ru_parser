import streamlit as st
import requests
from bs4 import BeautifulSoup as Bs
from fake_useragent import UserAgent
import sqlite3


def get_html(url, params=None):
    user_agent = UserAgent()
    headers = {"User-Agent": user_agent.random}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.text


def get_vacancies(html):
    soup = Bs(html, features="html.parser")
    vacancies = soup.find_all(class_='vacancy-search-item__card')
    try:
        vacancies_total = soup.select_one('div[data-qa*="vacancies-search-header"]').get_text()
    except AttributeError:
        vacancies_total = "Вакансии не найдены"
    vacancies_list = []
    for vacancy in vacancies:
        soup2 = Bs(str(vacancy), features="html.parser")
        vacancy_name = soup2.select_one('span[class*="vacancy-name"]').get_text()
        try:
            vacancy_salary = soup2.select_one('span[class*="compensation-text"]').get_text()
        except AttributeError:
            vacancy_salary = "Не указана"
        vacancy_company = soup2.select_one('span[class*="company-info-text"]').get_text()
        vacancy_region = soup2.select_one('span[data-qa*="vacancy-serp__vacancy-address"]').get_text()
        vacancies_list.append(([vacancy_name, vacancy_salary, vacancy_company, vacancy_region]))
    return vacancies_list, vacancies_total


def interface():
    st.title("Парсер вакансий на hh.ru")
    url = "https://hh.ru/search/vacancy"
    query = st.text_input("Введите запрос")
    params = {"text": query, "area": 1, "page": 0}
    parse_pages = st.slider("Сколько страниц парсить?", step=1, min_value=1, max_value=40)
    parse_button = st.button("Спарсить и записать в БД")
    vacancies_total = ""
    st.write(vacancies_total)
    filter_dict = {"Полный день": "fullDay", "Сменный график": "shift", "Гибкий график": "flexible",
                   "Вахтовый метод": "flyInFlyOut", "Удаленная работа": "remote", "Без опыта": "noExperience",
                   "От 1 до 3 лет": "between1And3", "От 3 до 6 лет": "between3And6", "Более 6 лет": "moreThan6",
                   "Не указано или не требуется": "not_required_or_not_specified", "Высшее": "higher",
                   "Среднее профессиональное": "special_secondary", "Полная занятость": "full",
                   "Частичная занятость": "part", "Стажировка": "probation", "Проектная работа": "project",
                   "Волонтерство": "volunteer"}
    salary_filter = st.toggle("Фильтровать по зарплате")
    if salary_filter:
        min_salary = st.number_input("Зарплата от", step=1000, min_value=0)
        params.update({"salary": min_salary})
    schedule_filter = st.toggle("Фильтровать по графику")
    if schedule_filter:
        schedule = st.multiselect("График работы", ["Полный день", "Сменный график", "Гибкий график", "Вахтовый метод", "Удаленная работа"])
        params.update({"schedule": list(map(filter_dict.get, schedule))})
    experience_filter = st.toggle("Фильтровать по опыту")
    if experience_filter:
        experience = st.multiselect("Требуемый опыт", ["Без опыта", "От 1 до 3 лет", "От 3 до 6 лет", "Более 6 лет"])
        params.update({"experience": list(map(filter_dict.get, experience))})
    education_filter = st.toggle("Фильтровать по образованию")
    if education_filter:
        education = st.multiselect("Требуемое образование", ["Не указано или не требуется", "Высшее", "Среднее профессиональное"])
        params.update({"education": list(map(filter_dict.get, education))})
    employment_filter = st.toggle("Фильтровать по типу занятости")
    if employment_filter:
        employment = st.multiselect("Тип занятости", ["Полная занятость", "Частичная занятость", "Стажировка", "Проектная работа", "Волонтерство"])
        params.update({"employment": list(map(filter_dict.get, employment))})

    if parse_button:
        for page in range(parse_pages):
            params["page"] = page
            html_page = get_html(url, params=params)
            vacancies_list, vacancies_total = get_vacancies(html_page)
            db_write(vacancies_list)


def db_write(vacancies):
    conn = sqlite3.connect("vacancies.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vacancies
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           title TEXT,
                           salary TEXT,
                           company TEXT,
                           location TEXT)''')
    cursor.executemany('INSERT INTO vacancies (title, salary, company, location) VALUES (?, ?, ?, ?)', vacancies)
    conn.commit()
    conn.close()


interface()
