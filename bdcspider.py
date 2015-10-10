#!/usr/bin/env python
#coding:utf-8

from collections import deque
from selenium import webdriver
from selenium import common
import time
import locale
import signal
import sys

DDEBUG=0
VERSION=0.1
APP="bdcspider"

#event flags
FLAG_EV_FETCH_SOURCE=1
FLAG_EV_FETCH_DATA=2

BASEURL="http://yun.baidu.com"
SOURCE_FIRST=BASEURL+"/share/home?uk=1828987782"

#sourcelist
SOURCEVIEW_ID="infiniteListView"
SOURCEVIEWLIST_CLASS="clearfix"
SOURCEURL_ATTR="_link"
SHARETIME_CLASS="time-col"

#paging
PAGEVIEW_ID="inifiniteListViewPage"
PAGESIZE1_CLASS="paging"
PAGESIZE_CLASS="page-all"
CURPAGE="page-input"
PAGENEXT="page-next"

#userinfo
FLAG_SOURCE_USE=1
FLAG_SOURCE_UNUSE=0
USERNAME_CLASS="brieftext"
USERNAME_CLASS2="homepagelink"
USERINFO_CLASS="sharenum"
SHARESIZE_ID="sharecnt_cnt"
ALBUMSIZE_ID="albumcnt_cnt"
SUBSIZE_CLASS="concerncnt"
LISTENERSIZE_CLASS="fanscnt"
HREF="href"

#piecelist
PIECE_CLASS="personage-panel"
PIECE_CLASS2="share-personage-item"
PIECE_USERNAME_CLASS="share-personage-name"
PIECE_PANEL_CLASS="share-personage-msg"
PIECE_PANEL_CLASS2="a[target=\"_blank\"]"
PIECE_SHARE=0
PIECE_ALBUM=1
PIECE_SUB=2
PIECE_LISTENER=3

#-------------------helper--------------------------

BI=u"\u4ebf" #for "亿"
MI=u"\u4e07" #for "万"
TI=u"\u5343" #for "千"
HI=u"\u767e" #for "百"
TEI=u"\u5341" #for "十"
CHARTOINT={BI:"00000000",MI:"0000",TI:"000",HI:"00",TEI:"0"}

def tointhelper(str):
    if(not isinstance(str,unicode)):
        if(DDEBUG):
            print "tointhelper:not unicode" #todo if it was not unicode
            return int(str)
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

#-------------------end helper----------------------

def signal_handler(signal, frame):
    sp.stat()
    sys.exit(0)

class userinfo:
    def __init__(self):
        self.flag=FLAG_SOURCE_UNUSE
        self.name=None
        self.sharesize=None
        self.shareurl=None
        self.albumsize=None
        self.albumurl=None
        self.subscribesize=None
        self.subcribeurl=None
        self.listenersize=None
        self.listenerurl=None

class sourcedata:
    def __init__(self,n,u):
        self.name=n
        self.url=u
        self.sharetime=None

class dbwriter:
    def __init__(self):
        pass

    def dbwrite(self,flist):
        self.dbprint(flist)

    def dbprint(self,flist):
        if(DDEBUG):
            for f in flist:
                print "name:%s url:%s sharetime:%s" % (f.name,f.url,f.sharetime)

class ev:
    def __init__(self,data):
        self.cbs=dict()
        self.data=data

    def addlistener(self,flag,listener):
        self.cbs[flag]=listener

    def loop(self):
        sp=self.data
        queue=sp.uiqueue
        cbs=self.cbs
        while(len(queue)>0):
            print "\nthere are %d sources in queue" % len(queue)
            src=queue.popleft()
            cb=cbs[FLAG_EV_FETCH_DATA]
            if(cb):
                cb(src,self.data)
            cb=cbs[FLAG_EV_FETCH_SOURCE]
            if(cb):
                cb(src,self.data)
        print "there are %d sources in queue" % len(queue)


class baidufetch:
    def __init__(self):
        self.browser=None
        self.sp=None

    def start(self):
        self.browser = webdriver.Firefox()

    def getpieces(self):
        b=self.browser
        count=0
        pindex=None

        try:
            pagesize=self.getpanelpagesize()
            pagesize=int(pagesize)
        except common.exceptions.NoSuchElementException,e:
            if(DDEBUG):
                print "only one page"
            pagesize=1
        if(pagesize<=0):
            return
        print "total %d pages" % (pagesize)

        while(count<pagesize):
            v1=b.find_element_by_class_name(PIECE_CLASS)
            v2=v1.find_elements_by_class_name(PIECE_CLASS2)
            pindex=0
            while(pindex<len(v2)):
                #parse one userpiece to userinfo
                elem=v2[pindex]
                vu=elem.find_element_by_class_name(PIECE_USERNAME_CLASS)
                v3=elem.find_element_by_class_name(PIECE_PANEL_CLASS)
                v4=v3.find_elements_by_css_selector(PIECE_PANEL_CLASS2)
                srcadd=userinfo()
                srcadd.name=vu.text
                srcadd.sharesize=v4[PIECE_SHARE].find_elements_by_xpath("b")[0].text
                srcadd.shareurl=v4[PIECE_SHARE].get_attribute(HREF)    
                srcadd.albumsize=v4[PIECE_ALBUM].find_elements_by_xpath("b")[0].text
                srcadd.albumurl=v4[PIECE_ALBUM].get_attribute(HREF)    
                srcadd.subscribesize=v4[PIECE_SUB].find_elements_by_xpath("b")[0].text
                srcadd.subcribeurl=v4[PIECE_SUB].get_attribute(HREF)
                srcadd.listenersize=v4[PIECE_LISTENER].find_elements_by_xpath("b")[0].text
                srcadd.listenerurl=v4[PIECE_LISTENER].get_attribute(HREF)
                srcadd.sharesize=tointhelper(srcadd.sharesize)
                srcadd.albumsize=tointhelper(srcadd.albumsize)
                srcadd.subscribesize=tointhelper(srcadd.subscribesize)
                srcadd.listenersize=tointhelper(srcadd.listenersize)    #todo:if size was chinese represent then failed
                srcadd.flag=FLAG_SOURCE_UNUSE

                if(DDEBUG):
                    print "getuserinfo name:%s sharesize:%d albumsize:%d subsize:%d listenersize:%d shareurl:%s" % (srcadd.name,srcadd.sharesize,srcadd.albumsize,srcadd.subscribesize,srcadd.listenersize,srcadd.shareurl)
                self.sp.uiqueue.append(srcadd)
                pindex+=1

            print "fetch %d userinfo in page%d" % ((pindex+1),(count+1))
            if(pagesize>1):
                nextpage=self.getpanelnextpage()
                nextpage.click()
                time.sleep(2)
            count+=1

    def fetchuserinfo(self,src,data):
        b=self.browser
        if(src.subscribesize>0):
            print "goto subscribeurl"
            b.get(src.subcribeurl)
            time.sleep(8)
            self.getpieces()

        if(src.listenersize>0):
            print "goto listenerurl"
            b.get(src.listenerurl)
            time.sleep(8)
            self.getpieces()

    def getpanelnextpage(self):
        b=self.browser
        pc=b.find_element_by_class_name("personage-panel")
        pi=pc.find_element_by_id("personagePage")
        pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
        nextpage=pc1.find_element_by_class_name(PAGENEXT)
        return nextpage

    def getpanelpagesize(self):
        b=self.browser
        b.switch_to.frame(0)
        pc=b.find_element_by_class_name("personage-panel")
        pi=pc.find_element_by_id("personagePage")
        pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
        pagesize=pc1.find_element_by_class_name(PAGESIZE_CLASS).text
        return pagesize

    def getnextpage(self):
        pi=self.browser.find_element_by_id(PAGEVIEW_ID)
        pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
        nextpage=pc1.find_element_by_class_name(PAGENEXT)
        return nextpage

    def getpagesize(self):
        pi=self.browser.find_element_by_id(PAGEVIEW_ID)
        pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
        pagesize=pc1.find_element_by_class_name(PAGESIZE_CLASS).text
        return pagesize

    def parseuser(self,src):
        b=self.browser
        v1=b.find_element_by_class_name(USERNAME_CLASS)
        v2=v1.find_element_by_class_name(USERNAME_CLASS2)
        src.name=v2.text

        v1=b.find_element_by_class_name(USERINFO_CLASS)
        v2=v1.find_element_by_id(SHARESIZE_ID)
        src.sharesize=tointhelper(v2.text)

        v2=v1.find_element_by_id(ALBUMSIZE_ID)
        src.albumsize=tointhelper(v2.text)

        v2=v1.find_elements_by_class_name(SUBSIZE_CLASS)
        src.subscribesize=tointhelper(v2[1].text)
        src.subcribeurl=v2[0].get_attribute(HREF)
            
        v2=v1.find_elements_by_class_name(LISTENERSIZE_CLASS)
        src.listenersize=tointhelper(v2[1].text)
        src.listenerurl=v2[0].get_attribute(HREF)

        src.flag=FLAG_SOURCE_USE
        
        if(DDEBUG):
            print "parseuser name:%s sharesize:%s albumsize:%s subsize:%d listenersize:%d url:%s" % (src.name,src.sharesize,src.albumsize,src.subscribesize,src.listenersize,src.listenerurl)

    def finish(self):
        self.browser.quit()

    def fetchsrcdata(self,src,data):
        sp=data
        b=self.browser
        flist=[]
        fsize=0

        b.get(src.shareurl)
        if(src.flag==FLAG_SOURCE_UNUSE):
            self.parseuser(src)
        print "goto %s sourcelist" % (src.name)

        try:
            pagesize=self.getpagesize()
            pagesize=int(pagesize)
        except common.exceptions.NoSuchElementException,e:
            if(DDEBUG):
                print "only one page"
            pagesize=1
        if(pagesize<=0):
            return
        print "total %d pages" % (pagesize)
        count=0
        while(count<pagesize):
            se=b.find_element_by_id(SOURCEVIEW_ID) 
            selist=se.find_elements_by_class_name(SOURCEVIEWLIST_CLASS)
            for elem in selist:
               fd=sourcedata(elem.text,elem.get_attribute(SOURCEURL_ATTR))
               fd.sharetime=elem.find_element_by_class_name(SHARETIME_CLASS).text
               flist.append(fd)
            if pagesize>1:
                nextpage=self.getnextpage()
                nextpage.click()
                time.sleep(2)
            fsize+=len(selist)
            print "fetch %d sources in page%d" % (fsize,(count+1))
            if(sp.dbwriter):
                sp.dbwriter.dbwrite(flist)
            count+=1

        if(src.sharesize>fsize):
            sp.dropsrcs=src.sharesize-fsize
        elif(src.sharesize<fsize):
            print "maybe user shares new when fetching..."
        sp.fetchsrcs+=fsize

class spider:
    def __init__(self):
        self.uiqueue=deque([])
        self.ev=ev(self)
        self.start_time=time.time()
        self.end_time=None
        self.fetch=None
        self.fetchsrcs=0
        self.dropsrcs=0
        self.dropuser=0
        self.dbwriter=None

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

    def start(self):
        self.fetch.start()
        self.ev.loop()

    def stat(self):
        self.end_time=time.time()
        print "-------------------------stat-----------------------------"
        print "fetchs:%d drops:%d" % (self.fetchsrcs,self.dropsrcs)
        print "run time %ds" % (self.end_time-self.start_time)
        print "----------------------------------------------------------"

    def finish(self):
        self.stat()
        self.fetch.finish()

sp=spider()

def main():
    signal.signal(signal.SIGINT, signal_handler)
    fe=baidufetch()
    ev=sp.ev
    ev.addlistener(FLAG_EV_FETCH_SOURCE,fe.fetchuserinfo)
    ev.addlistener(FLAG_EV_FETCH_DATA,fe.fetchsrcdata)
    dbw=dbwriter()
    sp.addfetcher(fe)
    sp.adddbwriter(dbw)

    firstsrc=userinfo()
    firstsrc.shareurl=SOURCE_FIRST
    sp.uiqueue.append(firstsrc)
    sp.show()
    sp.start()
    sp.finish()

if __name__=="__main__":
    main()
