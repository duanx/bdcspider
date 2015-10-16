#!/usr/bin/env python
# coding:utf-8
__author__ = 'lixin'
'''
��װMySQL
����ֱ�Ӵ�MySQL�ٷ���վ�������µ�Community Server 5.6.x�汾��MySQL�ǿ�ƽ̨�ģ�ѡ���Ӧ��ƽ̨���ذ�װ�ļ�����װ���ɡ�
��װʱ��MySQL����ʾ����root�û��Ŀ������ؼ����������¼ǲ�ס���Ͱѿ�������Ϊpassword��
��Windows�ϣ���װʱ��ѡ��UTF-8���룬�Ա���ȷ�ش������ġ�
��Mac��Linux�ϣ���Ҫ�༭MySQL�������ļ��������ݿ�Ĭ�ϵı���ȫ����ΪUTF-8��MySQL�������ļ�Ĭ�ϴ����/etc/my.cnf����/etc/mysql/my.cnf��
[client]
default-character-set = utf8
[mysqld]
default-storage-engine = INNODB
character-set-server = utf8
collation-server = utf8_general_ci
����MySQL�󣬿���ͨ��MySQL�Ŀͻ��������м����룺
$ mysql -u root -p
Enter password:
Welcome to the MySQL monitor...
...
mysql> show variables like '%char%';
+--------------------------+--------------------------------------------------------+
| Variable_name            | Value                                                  |
+--------------------------+--------------------------------------------------------+
| character_set_client     | utf8                                                   |
| character_set_connection | utf8                                                   |
| character_set_database   | utf8                                                   |
| character_set_filesystem | binary                                                 |
| character_set_results    | utf8                                                   |
| character_set_server     | utf8                                                   |
| character_set_system     | utf8                                                   |
| character_sets_dir       | /usr/local/mysql-5.1.65-osx10.6-x86_64/share/charsets/ |
+--------------------------+--------------------------------------------------------+
8 rows in set (0.00 sec)
����utf8�����ͱ�ʾ����������ȷ��
'''

# ��Ҫ��װMYSQL����,ָ�����£�
# $ pip install mysql-connector-python --allow-external mysql-connector-python

# ����:

# 导入:
import uuid
from datetime import datetime
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 创建对象的基类:
Base = declarative_base()
# 初始化数据库连接:
engine = create_engine('mysql+mysqlconnector://root:Duanx1234@localhost:3306/test')
# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)

class Sourcedata(Base):
    # 表的名字:
    __tablename__ = 'sourcedata'

    # 表的结构
    id = Column(String(50), primary_key=True)
    name = Column(String(500))
    url = Column(String(500))
    sharetime = Column(String(20))
    createtime = Column(String(20))

class SourcedataDao:
    def batchInsert(self, flist):
        try:
            # 创建session对象:
            session = DBSession()
            for sd in flist:
                # 创建新Sourcedata对象:
                new_sourcedata = Sourcedata(id=str(uuid.uuid4()), name=sd.name, url=sd.url, sharetime=sd.sharetime, createtime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                # 添加到session:
                session.add(new_sourcedata)
                print "insert a new_sourcedata"
            # 提交即保存到数据库:
            session.commit()
        except Exception,e:
            print e.message
        finally:
            # 关闭session:
            session.close()

class sdata:
    def __init__(self,n,u):
        self.name=n
        self.url=u
        self.sharetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S')

if __name__ == "__main__":
    flist = []
    sdDao = SourcedataDao()
    for i in range(10):
        flist.append(sdata("file" + str(i), "pan.baidu.com/file" + str(i)))
    sdDao.batchInsert(flist)

