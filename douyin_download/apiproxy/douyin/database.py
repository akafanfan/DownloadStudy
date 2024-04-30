#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sqlite3
import json
import sys
import datetime


class DataBase(object):
    def __init__(self):
        self.conn = sqlite3.connect('./douyin.db')
        self.cursor = self.conn.cursor()
        self.create_user_post_table()
        self.create_user_like_table()
        self.create_mix_table()
        self.create_music_table()
        self.create_user_all_record_table()

    # get_d_user_all_record
    # 根据uid 和 name 查询get_d_user_all_record表
    def select_d_user_all_record(self, name: str):

        sql = """select name, aweme_count, update_time, status, uid, last_point from d_user_all_record  where name=?;"""
        try:
            self.cursor.execute(sql, (name,))
            self.conn.commit()
            res = self.cursor.fetchone()
            return res
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def insert_d_user_all_record(self, uid: str, name: str):
        insert_sql = """
            INSERT INTO d_user_all_record (name, aweme_count,create_time, update_time, status, uid, last_point)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        # 获取当前时间
        now_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.cursor.execute(insert_sql, (name, 0, now_datetime, now_datetime, 0, uid, 0))
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def update_d_user_all_record_uid(self, uid: str, name: str):
        update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = """
            UPDATE d_user_all_record
            SET uid=?, update_time=?
            WHERE name=?
        """
        try:
            self.cursor.execute(sql, (uid, update_time, name))
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def update_d_user_all_record_aweme_count(self, name: str, last_point: int, aweme_count: int):
        update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = """
            UPDATE d_user_all_record
            SET aweme_count=?, update_time=?,last_point=?
            WHERE name=?
        """
        try:
            self.cursor.execute(sql, (aweme_count, update_time, last_point, name))
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def create_user_all_record_table(self):
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS d_user_all_record (
                id  INTEGER  not null primary key autoincrement,
                name VARCHAR(100) NOT NULL,
                aweme_count INTEGER,
                create_time DATETIME,
                update_time DATETIME,
                status INTEGER,
                uid VARCHAR(200),
                last_point INTEGER
            );
        """

        create_name_index_sql = """
            CREATE INDEX IF NOT EXISTS name_index ON d_user_all_record (name);
        """

        create_uid_index_sql = """
            CREATE INDEX IF NOT EXISTS uid_index ON d_user_all_record (uid);
        """

        try:
            self.cursor.execute(create_table_sql)
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

        try:
            self.cursor.execute(create_name_index_sql)
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

        try:
            self.cursor.execute(create_uid_index_sql)
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def create_user_post_table(self):
        sql = """CREATE TABLE if not exists t_user_post (
                        id integer primary key autoincrement,
                        sec_uid varchar(200),
                        aweme_id integer unique, 
                        rawdata json
                    );"""

        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def get_user_post(self, sec_uid: str, aweme_id: int):
        sql = """select id, sec_uid, aweme_id, rawdata from t_user_post where sec_uid=? and aweme_id=?;"""

        try:
            self.cursor.execute(sql, (sec_uid, aweme_id))
            self.conn.commit()
            res = self.cursor.fetchone()
            return res
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def insert_user_post(self, sec_uid: str, aweme_id: int, data: dict):
        insertsql = """insert into t_user_post (sec_uid, aweme_id, rawdata) values(?,?,?);"""

        try:
            self.cursor.execute(insertsql, (sec_uid, aweme_id, json.dumps(data)))
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def create_user_like_table(self):
        sql = """CREATE TABLE if not exists t_user_like (
                        id integer primary key autoincrement,
                        sec_uid varchar(200),
                        aweme_id integer unique,
                        rawdata json
                    );"""

        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def get_user_like(self, sec_uid: str, aweme_id: int):
        sql = """select id, sec_uid, aweme_id, rawdata from t_user_like where sec_uid=? and aweme_id=?;"""

        try:
            self.cursor.execute(sql, (sec_uid, aweme_id))
            self.conn.commit()
            res = self.cursor.fetchone()
            return res
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def insert_user_like(self, sec_uid: str, aweme_id: int, data: dict):
        insertsql = """insert into t_user_like (sec_uid, aweme_id, rawdata) values(?,?,?);"""

        try:
            self.cursor.execute(insertsql, (sec_uid, aweme_id, json.dumps(data)))
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def create_mix_table(self):
        sql = """CREATE TABLE if not exists t_mix (
                        id integer primary key autoincrement,
                        sec_uid varchar(200),
                        mix_id varchar(200),
                        aweme_id integer,
                        rawdata json
                    );"""

        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def get_mix(self, sec_uid: str, mix_id: str, aweme_id: int):
        sql = """select id, sec_uid, mix_id, aweme_id, rawdata from t_mix where sec_uid=? and  mix_id=? and aweme_id=?;"""

        try:
            self.cursor.execute(sql, (sec_uid, mix_id, aweme_id))
            self.conn.commit()
            res = self.cursor.fetchone()
            return res
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def insert_mix(self, sec_uid: str, mix_id: str, aweme_id: int, data: dict):
        insertsql = """insert into t_mix (sec_uid, mix_id, aweme_id, rawdata) values(?,?,?,?);"""

        try:
            self.cursor.execute(insertsql, (sec_uid, mix_id, aweme_id, json.dumps(data)))
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def create_music_table(self):
        sql = """CREATE TABLE if not exists t_music (
                        id integer primary key autoincrement,
                        music_id varchar(200),
                        aweme_id integer unique,
                        rawdata json
                    );"""

        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def get_music(self, music_id: str, aweme_id: int):
        sql = """select id, music_id, aweme_id, rawdata from t_music where music_id=? and aweme_id=?;"""

        try:
            self.cursor.execute(sql, (music_id, aweme_id))
            self.conn.commit()
            res = self.cursor.fetchone()
            return res
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()

    def insert_music(self, music_id: str, aweme_id: int, data: dict):
        insertsql = """insert into t_music (music_id, aweme_id, rawdata) values(?,?,?);"""

        try:
            self.cursor.execute(insertsql, (music_id, aweme_id, json.dumps(data)))
            self.conn.commit()
        except Exception as e:
            print(f'\033[31m数据库操作异常:{e}\033[m')
            sys.exit()


if __name__ == '__main__':
    print(f'数据库操作异常')
