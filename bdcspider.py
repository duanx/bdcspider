#!/usr/bin/env python
#coding:utf-8

from collections import deque
from selenium import webdriver
from selenium import common
import time
import locale
import signal
import sys
from bdmysqlDB import SourcedataDao
import dbhash

DDEBUG=0
VERSION=0.8
APP="bdcspider"
DBSOURCE="bdcsources.txt"

#event flags
FLAG_EV_FETCH_USERINFO=1
FLAG_EV_FETCH_SOURCE=2

BASEURL="http://yun.baidu.com"
SOURCE_FIRST=BASEURL+"/share/home?uk=1864871638"

#sourcelist
SOURCEVIEW_ID="infiniteListView"
SOURCEVIEWLIST_CLASS="clearfix"
SOURCENAME_CLASS="file-col"
SOURCETITLE_ATTR="title"
SOURCEURL_ATTR="_link"
SHARETIME_CLASS="time-col"

#paging
PAGEVIEW_ID="inifiniteListViewPage"
PAGESIZE1_CLASS="paging"
PAGESIZE_CLASS="page-all"
CURPAGE="page-input"
PAGENEXT="page-next"

#userinfo
FLAG_UI_USE=1
FLAG_UI_UNUSE=0
FLAG_UI_IN_DICT=2
FLAG_UI_IN_DELDICT=3
FLAG_UI_NOT_IN_DICT=4

USERNAME_CLASS="brieftext"
USERNAME_CLASS2="homepagelink"
USERINFO_CLASS="sharenum"
SHARESIZE_ID="sharecnt_cnt"
ALBUMSIZE_ID="albumcnt_cnt"
SUBSIZE_CLASS="concerncnt"
LISTENERSIZE_CLASS="fanscnt"
HREF="href"

#panellist
PANEL_CLASS="personage-panel"
PANEL_CLASS2="share-personage-item"
PANEL_USERNAME_CLASS="share-personage-name"
PANEL_PANEL_CLASS="share-personage-msg"
PANEL_PANEL_CLASS2="a[target=\"_blank\"]"
PANEL_SHARE=0
PANEL_ALBUM=1
PANEL_SUB=2
PANEL_LISTENER=3
PANEL_PAGING_ID="personagePage"

#####################################################################################################

BI=u"\u4ebf" #for "äº¿"
MI=u"\u4e07" #for "ä¸‡"
TI=u"\u5343" #for "åƒ"
HI=u"\u767e" #for "ç™¾"
TEI=u"\u5341" #for "å"
CHARTOINT={BI:"00000000",MI:"0000",TI:"000",HI:"00",TEI:"0"}

def tointhelper(str):
    if(not isinstance(str,unicode)):
        if(DDEBUG):
            print "tointhelper:not unicode" #todo if it was not unicode
            return 0
    if(str.rfind(BI)!=-1):
        str=str.replace(HI,CHARTOINT[HI])
    elif(str.rfind(MI)!=-1):
        str=str.replace(MI,CHARTOINT[MI])
    elif(str.rfind(TI)!=-1):
        str=str.replace(TI,CHARTOINT[TI])
    elif(str.rfind(HI)!=-1):
        str=str.replace(HI,CHARTOINT[HI])
    elif(str.rfind(TEI)!=-1):
        str=str.replace(TEI,CHARTOINT[TEI])
    return int(str)

def signal_handler(signal, frame):
    sp.finish()
    print "quit."
    sys.exit(0)

def bdcpanic(msg):
    print "--------------------------------------------------------"
    print "bdcpanic [%s]" % (msg)
    print "--------------------------------------------------------"
    sys.exit(-1)


#####################################################################################################
URLDB="urldb"
USERDB="userdb"
FHUSERDB="fhuserdb"
class dbcache:
    def __init__(self,name):
        self.uc=dict()
        self.fn=name
        self.size=0

    def haskey(self,key):
        try:
            return self.uc[key];
        except KeyError,e:
            return None

    def setkv(self,key,val):
        try:
            self.uc[key]=val
            self.size+=1
        except KeyError,e:
            pass

    def save(self):
        try:
            dbh=dbhash.open(self.fn,"n")
        except Exception,e:
            bdcpanic(e)
        ks=self.uc.keys()
        for k in ks:
            k=str(k)
            dbh[k]=str(self.uc[k])
        dbh.sync()

    def clear(self):
        self.size=0
        self.uc.clear()

    def load(self):
        try:
            dbh=dbhash.open(self.fn,"r")
        except Exception,e:
            return
        if len(dbh) == 0:
            return
        item=dbh.first() #key for item[0],val for item[1]
        self.uc[str(item[0])]=str(item[1])
        self.size+=1
        for i in xrange(1, len(dbh)):
            item=dbh.next()
            self.uc[str(item[0])]=str(item[1])
            self.size+=1

#####################################################################################################
class userinfo:
    def __init__(self):
        self.flag=FLAG_UI_UNUSE
        self.name=None
        self.sharesize=0
        self.shareurl=None
        self.albumsize=0
        self.albumurl=None
        self.subscribesize=0
        self.subcribeurl=None
        self.listenersize=0
        self.listenerurl=None

    def getkey(self): 
        return str(self.sharesize) + " " + self.shareurl

    def setkey(self,key):
        assert key is not None
        split=key.split(" ")
        if len(split)!=2:
            bdcpanic("parse userinfo format failed");
        self.sharesize=int(split[0])
        self.shareurl=split[1]
        if DDEBUG:
            print "sharesize:%d shareurl:%s" % (self.sharesize,self.shareurl)

#####################################################################################################
class uidb: #userinfo database
    def __init__(self):
        self.uicache=dbcache(USERDB)
        self.fhcache=dbcache(FHUSERDB)
        self.uidict=dict() #running user database
        self.finishuidict=dict() #finished user database
        self.repusers=0
        self.dropusers=0

    def save(self):
        for u in self.uidict.values():
            self.uicache.setkv(u.getkey(),u.name)
        for u in self.finishuidict.values():
            self.fhcache.setkv(u.getkey(),u.name)
        self.uicache.save()
        print "saved userdb %d " % self.uicache.size
        self.fhcache.save()
        print "saved finished userdb %d " % self.fhcache.size

    def load(self):
        self.uicache.load()
        self.fhcache.load()
        for u in self.uicache.uc.keys():
            ui=userinfo()
            ui.setkey(u)
            ui.name=self.uicache.uc[u]
            ui.flag=FLAG_UI_UNUSE
            self.dbadd(ui)
        print "load %d userinfo in dbcache..." % self.uicache.size
        for u in self.fhcache.uc.keys():
            ui=userinfo()
            ui.setkey(u)
            ui.name=self.fhcache.uc[u]
            ui.flag=FLAG_UI_UNUSE
            self.finishuidict[ui.shareurl]=ui
        print "load %d finished userinfo in dbcache..." % self.fhcache.size

        self.uicache.clear()
        self.fhcache.clear()

    def size(self):
        return len(self.uidict)

    #todo O(n)
    def getmaxsharesize(self):
        ud=self.uidict
        assert len(ud) > 0
        uitems=ud.values()
        uimax=uitems[0]
        i=1
        l=len(uitems)

        while(i<l):
            if(uimax.sharesize<uitems[i].sharesize):
                uimax=uitems[i]
            i+=1
        return uimax

    def dbadd(self,user):# only in uidict,not finishuidict
        self.uidict[user.shareurl]=user

    def dbaddkv(self,key,val):# only in uidict,not finishuidict
        self.uidict[key]=val

    def dbdelkey(self,key):
        val=self.uidict.pop(key)
        self.finishuidict[key]=val

    def dbdel(self,user):
        self.dbdelkey(user.shareurl)

    def dbexists(self,user):
        try:
            if(self.uidict[user.shareurl]):
                if(DDEBUG):
                    print "%s exist in dict" % (user.name)
                self.repusers+=1
                return FLAG_UI_IN_DICT
        except KeyError,e:
            pass
        try:
            if(self.finishuidict[user.shareurl]):
                if(DDEBUG):
                    print "%s exist in deldict" % (user.name)
                self.dropusers+=1
                return FLAG_UI_IN_DELDICT
        except KeyError,e:
            pass
        return FLAG_UI_NOT_IN_DICT

#####################################################################################################
class sourcedata:
    def __init__(self,n,u):
        self.name=n
        self.url=u
        self.sharetime=None

#####################################################################################################
class dbwriter:
    def __init__(self,path=None):
        if path is not None:
            try:
                self.fd=open(path,"n")
            except IOError,e:
                bdcpanic(e)
        else:
            self.fd=None
            self.sdDao = SourcedataDao()

    def dbwrite(self,flist):
        self.__dbwrite(flist)

    def __dbwrite(self,flist):
        if(self.fd is None):
            self.sdDao.batchInsert(flist)
        else:
            for f in flist:
                name=f.name.encode("utf-8")
                url=f.url.encode("utf-8")
                st=f.sharetime.encode("utf-8")
                try:
                    self.fd.write("name:%s url:%s sharetime:%s\n" % (name,url,st))
                    self.fd.flush()
                except IOError,e:
                    bdcpanic(e)

    def finish(self):
        if self.fd is not None:
            self.fd.close()

#####################################################################################################
class ev:
    def __init__(self,data):
        self.cbs=dict() #event callback
        self.data=data #data for callback

    def addlistener(self,flag,listener):
        self.cbs[flag]=listener

    def loop(self):
        sp=self.data
        uidb=sp.uidb
        cbs=self.cbs #ÊÂ¼þ»Øµ÷
        
        while(uidb.size()>0):
            print "\nthere are %d userinfo in dict" % uidb.size()
            uimax=uidb.getmaxsharesize() #×î´ó¹²ÏíÊýÓÃ»§
            assert(uimax is not None)
            if(uimax.flag==FLAG_UI_UNUSE):#Ê×´ÎÔËÐÐ,ÏÈ½âÎö¸öÈË¶©ÔÄ/·ÛË¿Ïî
                sp.fetch.parseuser(uimax)

             #»ñÈ¡Ô´Êý¾Ý£¬
            cb=cbs[FLAG_EV_FETCH_SOURCE]
            if(cb):
                cb(uimax,self.data)

            #½âÎö¸öÈË¶©ÔÄ/·ÛË¿Ïî
            cb=cbs[FLAG_EV_FETCH_USERINFO]
            if(cb):
                cb(uimax,self.data)

            try:
                uidb.dbdel(uimax)
            except KeyError,e:
                bdcpanic(e)

        print "there are %d userinfo in dict" % uidb.size()

#####################################################################################################
class baidufetch:
    def __init__(self):
        self.browser=None
        self.sp=None
        self.clickelem=None #save element when clicking
        self.panelindex=0 #»ñÈ¡Êý¾Ý±¨´íÊ±,±£´æµ±Ç°index

    def start(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(10)

    def findhelper(self,callback,elem=None,data=None):
        assert callback is not None
        while True:
            try:
                ret=callback(self.browser,elem,data)
                break
            except Exception,e:
                print e
                time.sleep(2)
        return ret

    def clickhelper(self,elem):
        try:
            self.clickelem=elem
            elem.click()
            time.sleep(2)
        except Exception,e:
            print e
            self.clickhelper(elem)
 
    def goto(self,url):
        try:
            self.browser.get(url)
            time.sleep(2)
        except Exception,e:
            self.goto(url)

    def getpanel(self,curuser): #»ñÈ¡¸öÈË¶©ÔÄ/·ÛË¿ÏîÁÐ±í
        b=self.browser
        count=0
        pindex=None
        uidb=self.sp.uidb

        pagesize=self.getpanelpagesize()
        assert (pagesize>0)
        print "total %d pages" % (pagesize)

        while(count<pagesize):
            def _getpanel(browser,el,data):
                fe=data
                sp=fe.sp

                v1=browser.find_element_by_class_name(PANEL_CLASS)
                v2=v1.find_elements_by_class_name(PANEL_CLASS2)
                pindex=0
                #»Ö¸´panelindex
                if fe.panelindex is not 0:
                    pindex=fe.panelindex

                while(pindex<len(v2)):
                    #parse one userdata to userinfo
                    elem=v2[pindex]
                    vu=elem.find_element_by_class_name(PANEL_USERNAME_CLASS)
                    v3=elem.find_element_by_class_name(PANEL_PANEL_CLASS)
                    v4=v3.find_elements_by_css_selector(PANEL_PANEL_CLASS2)
                    useradd=userinfo()
                    useradd.name=vu.text
                    useradd.sharesize=v4[PANEL_SHARE].find_elements_by_xpath("b")[0].text
                    useradd.shareurl=v4[PANEL_SHARE].get_attribute(HREF)    
                    useradd.albumsize=v4[PANEL_ALBUM].find_elements_by_xpath("b")[0].text
                    useradd.albumurl=v4[PANEL_ALBUM].get_attribute(HREF)    
                    useradd.subscribesize=v4[PANEL_SUB].find_elements_by_xpath("b")[0].text
                    useradd.subcribeurl=v4[PANEL_SUB].get_attribute(HREF)
                    useradd.listenersize=v4[PANEL_LISTENER].find_elements_by_xpath("b")[0].text
                    useradd.listenerurl=v4[PANEL_LISTENER].get_attribute(HREF)
                    useradd.sharesize=tointhelper(useradd.sharesize)
                    useradd.albumsize=tointhelper(useradd.albumsize)
                    useradd.subscribesize=tointhelper(useradd.subscribesize)
                    useradd.listenersize=tointhelper(useradd.listenersize)
                    useradd.flag=FLAG_UI_USE
                    fe.panelindex=pindex
                    
                    if(DDEBUG):
                        print "getuserinfo name:%s sharesize:%d albumsize:%d subsize:%d listenersize:%d shareurl:%s" % (useradd.name,useradd.sharesize,useradd.albumsize,useradd.subscribesize,useradd.listenersize,useradd.shareurl)

                    if(curuser.shareurl==useradd.shareurl): #¹ýÂË×Ô¼º
                        pindex+=1
                        continue
                    ret=uidb.dbexists(useradd)
                    if ret != FLAG_UI_IN_DELDICT: 
                        uidb.dbadd(useradd)
                    pindex+=1
                fe.panelindex=0
                return pindex

            size=self.findhelper(_getpanel,elem=None,data=self)
            print "fetch %d userinfo in page%d totalpage:%d" % (size,(count+1),pagesize)
            if(pagesize>1):
                nextpage=self.getpanelnextpage()
                self.clickhelper(nextpage)
            count+=1

    def fetchuserinfo(self,user,data):
        b=self.browser
        if(user.subscribesize>0):
            print "goto subscribeurl"
            self.goto(user.subcribeurl)
            self.getpanel(user)

        #if(user.listenersize>0):
        #    print "goto listenerurl"
        #    self.goto(user.listenerurl)
        #    self.getpanel(user)

    def getpanelnextpage(self):
        def _getpage(browser,elem=None,data=None):
            pc=browser.find_element_by_class_name(PANEL_CLASS)
            pi=pc.find_element_by_id(PANEL_PAGING_ID)
            pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
            nextpage=pc1.find_element_by_class_name(PAGENEXT)
            return nextpage
        nextpage=self.findhelper(_getpage)

        return nextpage

    def getpanelpagesize(self):
        b=self.browser
        def _getpanelpagesize(browser,elem=None,data=None):
            try:
                browser.switch_to.frame(0)
                pc=browser.find_element_by_class_name(PANEL_CLASS)
                pi=pc.find_element_by_id(PANEL_PAGING_ID)
                pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
                pagesize=pc1.find_element_by_class_name(PAGESIZE_CLASS).text
            except common.exceptions.NoSuchElementException,e:
                if(DDEBUG):
                    print "only one page"
                pagesize=1
            return pagesize
        pagesize=self.findhelper(_getpanelpagesize)
        pagesize=int(pagesize)
        return pagesize

    def getnextpage(self):
        def _getnextpage(browser,elem=None,data=None):
            pi=self.browser.find_element_by_id(PAGEVIEW_ID)
            pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
            nextpage=pc1.find_element_by_class_name(PAGENEXT)
            return nextpage
        nextpage=self.findhelper(_getnextpage)
        return nextpage

    def getpagesize(self):
        def _getpagesize(browser,elem=None,data=None):
            try:
                pi=browser.find_element_by_id(PAGEVIEW_ID)
                pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
                pagesize=pc1.find_element_by_class_name(PAGESIZE_CLASS).text
            except common.exceptions.NoSuchElementException,e:
                if(DDEBUG):
                    print "only one page"
                pagesize=1
            return pagesize
        pagesize=self.findhelper(_getpagesize)
        pagesize=int(pagesize)
        return pagesize

    def parseuser(self,user): #Í¨¹ýurl»ñÈ¡ÓÃ»§¹²ÏíÊý£¬¶©ÔÄ/·ÛË¿Ïî
        b=self.browser
        uidb=self.sp.uidb

        self.goto(user.shareurl)

        def _parseuser(browser,elem=None,data=None):
            user=data
            v1=browser.find_element_by_class_name(USERNAME_CLASS)
            v2=v1.find_element_by_class_name(USERNAME_CLASS2)
            user.name=v2.text

            v1=b.find_element_by_class_name(USERINFO_CLASS)
            v2=v1.find_element_by_id(SHARESIZE_ID)
            user.sharesize=tointhelper(v2.text)

            v2=v1.find_element_by_id(ALBUMSIZE_ID)
            user.albumsize=tointhelper(v2.text)

            v2=v1.find_elements_by_class_name(SUBSIZE_CLASS)
            user.subscribesize=tointhelper(v2[1].text)
            user.subcribeurl=v2[0].get_attribute(HREF)

            v2=v1.find_elements_by_class_name(LISTENERSIZE_CLASS)
            user.listenersize=tointhelper(v2[1].text)
            user.listenerurl=v2[0].get_attribute(HREF)

            user.flag=FLAG_UI_USE
            return user

        user=self.findhelper(_parseuser,elem=None,data=user)

        if(DDEBUG):
            print "parseuser name:%s sharesize:%s albumsize:%s subsize:%d listenersize:%d url:%s" % (user.name,user.sharesize,user.albumsize,user.subscribesize,user.listenersize,user.listenerurl)

    def finish(self):
        self.browser.quit()

    def fetchsrcdata(self,src,data):
        sp=data
        b=self.browser
        flist=[]
        fsize=0
        count=0

        print "goto %s sourcelist" % (src.name)
        self.goto(src.shareurl)

        pagesize=self.getpagesize()
        assert (pagesize>0)
        print "total %d pages" % (pagesize)
        def _getsrc(browser,elem=None,data=None):
            elemsize=0
            se=browser.find_element_by_id(SOURCEVIEW_ID) 
            selist=se.find_elements_by_class_name(SOURCEVIEWLIST_CLASS)
            for elem in selist:
                title=elem.find_element_by_class_name(SOURCENAME_CLASS)
                fd=sourcedata(title.get_attribute(SOURCETITLE_ATTR),elem.get_attribute(SOURCEURL_ATTR))
                fd.sharetime=elem.find_element_by_class_name(SHARETIME_CLASS).text
                if sp.dbcache.haskey(fd.url) is not None:
                    print "filter repeat url:%s" % fd.url
                    continue
                sp.dbcache.setkv(fd.url,1)
                elemsize+=1
                flist.append(fd)
            return elemsize
        while(count<pagesize):
            elemsize=self.findhelper(_getsrc)
            if pagesize>1:
                nextpage=self.getnextpage()
                self.clickhelper(nextpage)
            fsize+=elemsize
            print "fetch %d sources in page%d totalpage:%d" % (elemsize,(count+1),pagesize)
            if(sp.dbwriter):
                sp.dbwriter.dbwrite(flist)
            del flist[0:len(flist)]
            count+=1

        if(src.sharesize>fsize):
            sp.dropsrcs=src.sharesize-fsize
        sp.fetchsrcs+=fsize

#####################################################################################################
class spider:
    def __init__(self):
        self.uidb=uidb()
        self.ev=ev(self)
        self.start_time=time.time()
        self.end_time=None
        self.fetch=None
        self.dbwriter=None
        self.fetchsrcs=0
        self.dropsrcs=0
        self.dbcache=dbcache(URLDB)

    def adddbwriter(self,w):
        self.dbwriter=w

    def addfetcher(self,fe):
        self.fetch=fe
        fe.sp=self

    def show(self):
        print "%s version:%s" % (APP,VERSION)
        print "build for fetching baidu cloud data"
        print "locale:",
        print locale.getdefaultlocale()

    def prestart(self):
        self.dbcache.load()
        print "load %d urls in dbcache..." % self.dbcache.size
        self.uidb.load()

    def start(self):
        self.fetch.start()
        self.ev.loop()

    def stat(self):
        self.end_time=time.time()
        print "-------------------------stat-----------------------------"
        print "fetchsources:%d dropsources:%d repeat users:%d drop users:%d" % (self.fetchsrcs,self.dropsrcs,self.uidb.repusers,self.uidb.dropusers)
        print "%d userinfo waiting,%d userinfo finished in userdb" % (len(self.uidb.uidict),len(self.uidb.finishuidict))
        print "save %d urls in dbcache..." % self.dbcache.size
        print "run time %ds" % (self.end_time-self.start_time)
        print "----------------------------------------------------------"

    def finish(self):
        self.dbcache.save()
        print "saved urldb %d " % self.dbcache.size
        self.uidb.save()

        self.stat()
        self.dbwriter.finish()
        #self.fetch.finish()  #todo exception when firefox quit

#####################################################################################################
sp=spider()
def main():
    reload(sys)
    sys.setdefaultencoding("utf-8")
    signal.signal(signal.SIGINT, signal_handler)
    fe=baidufetch()
    ev=sp.ev
    ev.addlistener(FLAG_EV_FETCH_USERINFO,fe.fetchuserinfo)
    ev.addlistener(FLAG_EV_FETCH_SOURCE,fe.fetchsrcdata)
    dbw=dbwriter()
    sp.addfetcher(fe)
    sp.adddbwriter(dbw)
    sp.show()
    sp.prestart()
    if sp.uidb.size() == 0:
        firstsrc=userinfo()
        firstsrc.flag=FLAG_UI_UNUSE
        firstsrc.shareurl=SOURCE_FIRST
        sp.uidb.dbaddkv(SOURCE_FIRST,firstsrc)

    sp.start()
    sp.finish()

if __name__=="__main__":
    main()

#####################################################################################################
