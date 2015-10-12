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
VERSION=0.2
APP="bdcspider"

#event flags
FLAG_EV_FETCH_USERINFO=1
FLAG_EV_FETCH_SOURCE=2

BASEURL="http://yun.baidu.com"
SOURCE_FIRST=BASEURL+"/share/home?uk=2335513473"

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

def clickhelper(elem):
    try:
        elem.click()
        time.sleep(3)
    except common.exceptions.StaleElementReferenceException,e:
        print e
        time.sleep(1)
        clickhelper(elem)
 
def goto(browser,url):
    browser.get(url)
    time.sleep(2)


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

#####################################################################################################
class uidb: #userinfo database
    def __init__(self):
        self.uidict=dict() #running user database
        self.finishuidict=dict() #run finished user database
        self.repusers=0
        self.dropusers=0

    def size(self):
        return len(self.uidict)

    #todo O(n)
    def getmaxsharesize(self):
        ud=self.uidict
        uitems=ud.values()
        uimax=uitems[0]
        i=1
        l=len(uitems)
        assert(len(uitems)>0)

        while(i<l):
            if(uimax.sharesize<uitems[i].sharesize):
                uimax=uitems[i]
            i+=1
        return uimax

    def dbadd(self,user):
        self.uidict[user.name]=user

    def dbaddkv(self,key,val):
        self.uidict[key]=val

    def dbdel(self,user):
        dbdelkey(self,user.name)

    def dbdelkey(self,key):
        val=self.uidict.pop(key)
        self.finishuidict[key]=val

    def dbexists(self,user):
        try:
            if(self.uidict[user.name]):
                if(DDEBUG):
                    print "%s exist in dict" % (user.name)
                self.repusers+=1
                return FLAG_UI_IN_DICT
        except KeyError,e:
            pass
        try:
            if(self.finishuidict[user.name]):
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
    def __init__(self,path):
        try:
            self.fd=open(path,"w")
        except IOError,e:
            bdcpanic(e)

    def dbwrite(self,flist):
        self.__dbwrite(flist)

    def __dbwrite(self,flist):
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

                cb=cbs[FLAG_EV_FETCH_USERINFO]
                if(cb):
                    cb(uimax,self.data)

                cb=cbs[FLAG_EV_FETCH_SOURCE]
                if(cb):
                    cb(uimax,self.data)
            else: #»ñÈ¡Ô´Êý¾Ý£¬½âÎö¸öÈË¶©ÔÄ/·ÛË¿Ïî
                cb=cbs[FLAG_EV_FETCH_SOURCE]
                if(cb):
                    cb(uimax,self.data)

                cb=cbs[FLAG_EV_FETCH_USERINFO]
                if(cb):
                    cb(uimax,self.data)
            try:
                uidb.udel(uimax.name)
            except KeyError,e:
                bdcpanic(e)

        print "there are %d userinfo in dict" % uidb.size()

#####################################################################################################
class baidufetch:
    def __init__(self):
        self.browser=None
        self.sp=None

    def start(self):
        self.browser = webdriver.Firefox()

    def getpanel(self,curuser): #»ñÈ¡¸öÈË¶©ÔÄ/·ÛË¿ÏîÁÐ±í
        b=self.browser
        count=0
        pindex=None
        sp=self.sp

        pagesize=self.getpanelpagesize()
        assert (pagesize>0)
        print "total %d pages" % (pagesize)

        while(count<pagesize):
            try:
                v1=b.find_element_by_class_name(PANEL_CLASS)
                v2=v1.find_elements_by_class_name(PANEL_CLASS2)
            except Exception,e:
                print e
                time.sleep(2)
                continue
            pindex=0
            while(pindex<len(v2)):
                #parse one userdata to userinfo
                elem=v2[pindex]
                try:
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
                except Exception,e:
                    print e
                    time.sleep(2)
                    continue

                useradd.sharesize=tointhelper(useradd.sharesize)
                useradd.albumsize=tointhelper(useradd.albumsize)
                useradd.subscribesize=tointhelper(useradd.subscribesize)
                useradd.listenersize=tointhelper(useradd.listenersize)
                useradd.flag=FLAG_UI_USE

                if(DDEBUG):
                    print "getuserinfo name:%s sharesize:%d albumsize:%d subsize:%d listenersize:%d shareurl:%s" % (useradd.name,useradd.sharesize,useradd.albumsize,useradd.subscribesize,useradd.listenersize,useradd.shareurl)

                if(curuser.name==useradd.name): #¹ýÂË×Ô¼º
                    pindex+=1
                    continue
                ret=sp.uidb.dbexists(useradd)
                if ret is not FLAG_UI_IN_DELDICT: 
                    sp.uidb.dbadd(useradd)
                pindex+=1

            print "fetch %d userinfo in page%d totalpage:%d" % (pindex,(count+1),pagesize)
            if(pagesize>1):
                nextpage=self.getpanelnextpage()
                clickhelper(nextpage)
            count+=1

    def fetchuserinfo(self,user,data):
        b=self.browser
        if(user.subscribesize>0):
            print "goto subscribeurl"
            goto(b,user.subcribeurl)
            self.getpanel(user)

        if(user.listenersize>0):
            print "goto listenerurl"
            goto(b,user.listenerurl)
            self.getpanel(user)

    def getpanelnextpage(self):
        b=self.browser
        while True:
            try:
                pc=b.find_element_by_class_name(PANEL_CLASS)
                pi=pc.find_element_by_id(PANEL_PAGING_ID)
                pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
                nextpage=pc1.find_element_by_class_name(PAGENEXT)
                break
            except Exception,e:
                print e
                time.sleep(2)
        return nextpage

    def getpanelpagesize(self):
        b=self.browser
        while True:
            try:
                b.switch_to.frame(0)
                pc=b.find_element_by_class_name(PANEL_CLASS)
                pi=pc.find_element_by_id(PANEL_PAGING_ID)
                pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
                pagesize=pc1.find_element_by_class_name(PAGESIZE_CLASS).text
                break
            except common.exceptions.NoSuchElementException,e:
                if(DDEBUG):
                    print "only one page"
                pagesize=1
                break
            except Exception,e:
                print e
                time.sleep(2)
        pagesize=int(pagesize)
        return pagesize

    def getnextpage(self):
        while True:
            try:
                pi=self.browser.find_element_by_id(PAGEVIEW_ID)
                pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
                nextpage=pc1.find_element_by_class_name(PAGENEXT)
                break
            except Exception,e:
                print e
                time.sleep(2)
        return nextpage

    def getpagesize(self):
        while True:
            try:
                pi=self.browser.find_element_by_id(PAGEVIEW_ID)
                pc1=pi.find_element_by_class_name(PAGESIZE1_CLASS)
                pagesize=pc1.find_element_by_class_name(PAGESIZE_CLASS).text
                break
            except common.exceptions.NoSuchElementException,e:
                if(DDEBUG):
                    print "only one page"
                pagesize=1
                break
            except Exception,e:
                print e
                time.sleep(2)
        pagesize=int(pagesize)
        return pagesize

    def parseuser(self,user): #Ê×´ÎÔËÐÐ£¬Í¨¹ýurl»ñÈ¡ÓÃ»§¹²ÏíÊý£¬¶©ÔÄ/·ÛË¿Ïî
        b=self.browser
        uidb=self.sp.uidb

        goto(b,user.shareurl)
        v1=b.find_element_by_class_name(USERNAME_CLASS)
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

        #repair first user's dict
        del uidb.uidict[user.shareurl]
        uidb.dbadd(user)
        user.flag=FLAG_UI_USE

        if(DDEBUG):
            print "parseuser name:%s sharesize:%s albumsize:%s subsize:%d listenersize:%d url:%s" % (src.name,src.sharesize,src.albumsize,src.subscribesize,src.listenersize,src.listenerurl)

    def finish(self):
        self.browser.quit()

    def fetchsrcdata(self,src,data):
        sp=data
        b=self.browser
        flist=[]
        fsize=0
        count=0

        print "goto %s sourcelist" % (src.name)
        goto(b,src.shareurl)

        pagesize=self.getpagesize()
        assert (pagesize>0)
        print "total %d pages" % (pagesize)
        while(count<pagesize):
            while True:
                try:
                    se=b.find_element_by_id(SOURCEVIEW_ID) 
                    selist=se.find_elements_by_class_name(SOURCEVIEWLIST_CLASS)
                    for elem in selist:
                        fd=sourcedata(elem.text,elem.get_attribute(SOURCEURL_ATTR))
                        fd.sharetime=elem.find_element_by_class_name(SHARETIME_CLASS).text
                        flist.append(fd)
                    break
                except Exception,e:
                    print e
                    time.sleep(2)

            if pagesize>1:
                nextpage=self.getnextpage()
                clickhelper(nextpage)
            fsize+=len(selist)
            print "fetch %d sources in page%d totalpage:%d" % (len(selist),(count+1),pagesize)
            if(sp.dbwriter):
                sp.dbwriter.dbwrite(flist)
            count+=1

        if(src.sharesize>fsize):
            sp.dropsrcs=src.sharesize-fsize
        elif(src.sharesize<fsize):
            print "maybe user shares new when fetching..."
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
        print "fetchsources:%d dropsources:%d repeat users:%d drop users:%d" % (self.fetchsrcs,self.dropsrcs,self.uidb.repusers,self.uidb.dropusers)
        print "%d userinfo waiting,%d userinfo finished in userdb" % (len(self.uidb.uidict),len(self.uidb.finishuidict))
        print "run time %ds" % (self.end_time-self.start_time)
        print "----------------------------------------------------------"

    def finish(self):
        self.stat()
        self.dbwriter.finish()
        #self.fetch.finish()  #todo exception when firefox quit


sp=spider()

#####################################################################################################
def main():
    signal.signal(signal.SIGINT, signal_handler)
    fe=baidufetch()
    ev=sp.ev
    ev.addlistener(FLAG_EV_FETCH_USERINFO,fe.fetchuserinfo)
    ev.addlistener(FLAG_EV_FETCH_SOURCE,fe.fetchsrcdata)
    dbw=dbwriter("bdcsources.txt")
    sp.addfetcher(fe)
    sp.adddbwriter(dbw)

    firstsrc=userinfo()
    firstsrc.flag=FLAG_UI_UNUSE
    firstsrc.shareurl=SOURCE_FIRST
    sp.uidb.dbaddkv(SOURCE_FIRST,firstsrc)
    sp.show()
    sp.start()
    sp.finish()

if __name__=="__main__":
    main()
#####################################################################################################
