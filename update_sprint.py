#!/usr/bin/python
import sys
import argparse
import datetime
# в 00:00 utc asana может не отвечать на запросы, ошибка 500 от сервера
import pandas as pd
import asana
from sqlalchemy import create_engine

# funcs
def change_date_format(task, field_name):
    new_date_str = None
    try:
        if task[field_name]!=None:
            date = datetime.datetime.strptime(task[field_name],"%Y-%m-%dT%H:%M:%S.%fZ")
            new_format = "%Y-%m-%d"
            new_date_str = date.strftime(new_format)
    except:
        print('error with field_name')
        # логирование error with field_name
        pass
    finally:
        return new_date_str

def get_created_at(task):
    field_name = 'created_at'
    new_date_str = change_date_format(task, field_name)
    return new_date_str

def get_completed_at(task):
    field_name = 'completed_at'
    new_date_str = change_date_format(task, field_name)
    return new_date_str

def get_modified_at(task):
    field_name = 'modified_at'
    new_date_str = change_date_format(task, field_name)
    return new_date_str

def get_first_section(task):
    section = None
    global project_name
    # используется глобальная переменная project_name, не знаю пока как передать, не развалив полиморфизм
    try:
        for membership in task['memberships']:
            if membership['project']['name'] == project_name:
                section = membership['section']['name']
    except:
        print('error with section')
        print(task['memberships'])
        # логирование error with section
        raise
        pass
    finally:
        return section


def get_assignee(task):
    assignee = None
    try:
        if task["assignee"]!=None:
            assignee = task["assignee"]["name"]
    except:
        print('error with assignee')
        # логирование error with assignee
        pass
    finally:
        return assignee


# get_fields
def get_easy_fields(task):
    easy_fields_names = {
        'Task ID':'gid',
        'Name':'name'
    }
    easy_fields={}

    for column_name, task_column_name in easy_fields_names.items():
        easy_fields[column_name] = task[task_column_name]

    return easy_fields

def get_complex_fields(task):
    complex_fields_functions = {
        'Created At':get_created_at,
        'Completed At':get_completed_at,
        'Last Modified':get_modified_at,
        'Section/Column':get_first_section,
        'Assignee':get_assignee
    }
    complex_fields = {}
    for column_name, function in complex_fields_functions.items():
        complex_fields[column_name] = function(task)

    return complex_fields

def get_custom_fields(task):
    all_custom_fields = {}
    for custom_field in task['custom_fields']:
        key = custom_field['name']
        value = None
        if 'number_value' in custom_field:
            value = custom_field['number_value']
        if 'enum_value' in custom_field:
            if custom_field['enum_value']!=None:
                value = custom_field['enum_value']['name']
        all_custom_fields[key] = value
    all_custom_fields

    some_custom_fields_names = {
        'PH Version':'PH Version',
        'PP Story Points':'PP Story Points',
        'PH Work Status':'PH Work Status',
        'PH Issue Type':'PH Issue Type',
        'PH Priority':'PH Priority',
        'PP GD Tag':'PP GD Tag'
    }
    some_custom_fields = {}
    for column_name, task_custom_field_column_name in some_custom_fields_names.items():
        # get возвращает параметр2(None), если не найдёт в словаре ключ.
        some_custom_fields[column_name] = all_custom_fields.get(task_custom_field_column_name, None)

    return some_custom_fields

def get_fields(task):
    task_fields = {}
    easy_fields = get_easy_fields(task)
    complex_fields = get_complex_fields(task)
    some_custom_fields = get_custom_fields(task)
    # python 3.9 минимальная версия для слияния словарей оператором |
    task_fields = easy_fields | complex_fields | some_custom_fields
    return task_fields


def points(df):
    result = None
    if df['PP Story Points']=='∞':
        result = None
        return result
    # нули заменяются дробными значениями, для получения 0 + 0 +...+ 0 ~= 1
    if df['PP Story Points']=='0':
        result = 0.334
        return result
    if df['PP Story Points']=='?':
        result = None
        return result
    # неактуальный случай вроде после того, как отказались от
    # по какой-то причине функции isnan() из math, pandas и numpy не работают
    # со всеми возможными значениями из столбца 'PP Story Points'
    # поэтому используется свойство, что nan не равны между самой и даже самому себе
    if df['PP Story Points']!=df['PP Story Points']:
        result = None
        return result
    if df['PP Story Points']==None:
        result = None
        return result
    if str.isnumeric(df['PP Story Points']):
        result = int(df['PP Story Points'])
        return result
    return result

def question_count(df):
    result = None
    if df['PP Story Points']=='?':
        result = 1
        return result
    return result

def createParser ():
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('phase')
    return parser

# main func
def main_func():
    parser = createParser()
    namespace = parser.parse_args()
    print (namespace.project, namespace.phase)
    global project_name
    project_name = namespace.project
    project_phase = namespace.phase # 'plan' or '1week' or 'fact'
    projects = {
        'Dev Sprint 13':'1200658883187949',
        'Dev Sprint 11':'1200529909447835',
        'Dev Sprint 14':'1200743636193024'
    }
    phases = ['plan', '1week', 'fact']

    if project_name not in projects:
        print('project_name not in allowed project_names. Allowed project names:')
        print(projects.keys())
        return

    if project_phase not in phases:
        print('phase not in allowed phases. Allowed phases:')
        print(phases)
        return

    # get security data
    PATasana = '******'

    login = 'slukin'
    password = '******'
    database_connect_info = 'collect.cdhj0rqdtwnc.us-east-1.redshift.amazonaws.com:5439/test'

    # today = datetime.datetime.now()
    # yesterday = today + datetime.timedelta(days=-1)
    # # "дата выгрузки" - сегодня, или вчера, если скрипт выполняется утром следующего дня
    # date = today # yesterday #
    # date_format = "%Y-%m-%d"
    # date_str = date.strftime(date_format)


    project_id = projects[project_name]

    schema ='temp_dash'
    table = 'asana_dev_sprint_plan_1week_fact'

    # main

    asana_client = asana.Client.access_token(PATasana)

    fields = [
        'assignee.name',
        'created_at',
        'completed_at',
        'modified_at',
        'name',
        'memberships.(project|section).name',
        'custom_fields'
    ]

    sprint = pd.DataFrame()

    try:
        tasks = asana_client.tasks.find_by_project(project_id, fields=fields)
        for task in tasks:
            task_fields = get_fields(task)
            sprint = sprint.append(task_fields, ignore_index=True)

        # доп поля для sprint
        sprint['points'] = sprint.apply(lambda x: points(x), axis=1)
        sprint['question count'] = sprint.apply(lambda x: question_count(x), axis=1)
        sprint['Sprint name'] = project_name
        sprint['plan/fact'] = project_phase
    except Exception:
        # ошибка от asana, нужно разобраться с выводом
        print(repr(Exception))
        print(Exception)
        print(Exception.args)


#     print(project_name, project_phase)
    engine = create_engine('postgresql+psycopg2://'+login+':'+password+'@'+database_connect_info)
    sql_delete = f'''
        DELETE FROM {schema}.{table}
        WHERE
            "Sprint name" = \'{project_name}\' AND
            "plan/fact" = \'{project_phase}\'
    '''
    engine.execute(sql_delete)
    sprint.to_sql( table, engine,schema=schema, if_exists='append', index=False, chunksize=1000)
    print('done')
    return

if __name__ == "__main__":
    main_func()

