#!/usr/bin/env python
# coding:utf-8
__author__ = 'lixin'
'''
°²×°MySQL
¿ÉÒÔÖ±½Ó´ÓMySQL¹Ù·½ÍøÕ¾ÏÂÔØ×îĞÂµÄCommunity Server 5.6.x°æ±¾¡£MySQLÊÇ¿çÆ½Ì¨µÄ£¬Ñ¡Ôñ¶ÔÓ¦µÄÆ½Ì¨ÏÂÔØ°²×°ÎÄ¼ş£¬°²×°¼´¿É¡£
°²×°Ê±£¬MySQL»áÌáÊ¾ÊäÈërootÓÃ»§µÄ¿ÚÁî£¬ÇëÎñ±Ø¼ÇÇå³ş¡£Èç¹ûÅÂ¼Ç²»×¡£¬¾Í°Ñ¿ÚÁîÉèÖÃÎªpassword¡£
ÔÚWindowsÉÏ£¬°²×°Ê±ÇëÑ¡ÔñUTF-8±àÂë£¬ÒÔ±ãÕıÈ·µØ´¦ÀíÖĞÎÄ¡£
ÔÚMac»òLinuxÉÏ£¬ĞèÒª±à¼­MySQLµÄÅäÖÃÎÄ¼ş£¬°ÑÊı¾İ¿âÄ¬ÈÏµÄ±àÂëÈ«²¿¸ÄÎªUTF-8¡£MySQLµÄÅäÖÃÎÄ¼şÄ¬ÈÏ´æ·ÅÔÚ/etc/my.cnf»òÕß/etc/mysql/my.cnf£º
[client]
default-character-set = utf8
[mysqld]
default-storage-engine = INNODB
character-set-server = utf8
collation-server = utf8_general_ci
ÖØÆôMySQLºó£¬¿ÉÒÔÍ¨¹ıMySQLµÄ¿Í»§¶ËÃüÁîĞĞ¼ì²é±àÂë£º
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
¿´µ½utf8×ÖÑù¾Í±íÊ¾±àÂëÉèÖÃÕıÈ·¡£
'''

# ĞèÒª°²×°MYSQLÇı¶¯,Ö¸ÁîÈçÏÂ£º
# $ pip install mysql-connector-python --allow-external mysql-connector-python

# µ¼Èë:

# å¯¼å…¥:
import uuid
from datetime import datetime
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# åˆ›å»ºå¯¹è±¡çš„åŸºç±»:
Base = declarative_base()
# åˆå§‹åŒ–æ•°æ®åº“è¿æ¥:
engine = create_engine('mysql+mysqlconnector://root:Duanx1234@localhost:3306/test')
# åˆ›å»ºDBSessionç±»å‹:
DBSession = sessionmaker(bind=engine)

class Sourcedata(Base):
    # è¡¨çš„åå­—:
    __tablename__ = 'sourcedata'

    # è¡¨çš„ç»“æ„
    id = Column(String(50), primary_key=True)
    name = Column(String(500))
    url = Column(String(500))
    sharetime = Column(String(20))
    createtime = Column(String(20))

class SourcedataDao:
    def batchInsert(self, flist):
        try:
            # åˆ›å»ºsessionå¯¹è±¡:
            session = DBSession()
            for sd in flist:
                # åˆ›å»ºæ–°Sourcedataå¯¹è±¡:
                new_sourcedata = Sourcedata(id=str(uuid.uuid4()), name=sd.name, url=sd.url, sharetime=sd.sharetime, createtime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                # æ·»åŠ åˆ°session:
                session.add(new_sourcedata)
                print "insert a new_sourcedata"
            # æäº¤å³ä¿å­˜åˆ°æ•°æ®åº“:
            session.commit()
        except Exception,e:
            print e.message
        finally:
            # å…³é—­session:
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


