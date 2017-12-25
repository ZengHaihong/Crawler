
# coding: utf-8

# # 自动获取ip

# In[213]:

import requests
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError,Timeout,ConnectionError,ChunkedEncodingError
import time
import re
import multiprocessing
from multiprocessing.dummy import Pool
import random


# In[240]:

class Ip_pool():
    '''
    这是一个获取可用的ip池的类
    
    功能
    -----
    获取西刺代理高匿代理ip
    
    属性
    -----
    ip_url_ls:字符串，代理ip的爬取页面初始页面
    
    方法
    -----
    1.check_chinese(self,check_str): 检查ip地址是否含中文字符
    2.visit_url(self,ip_url,prox_ip=None):访问西刺代理ip，获得BeautifulSoup
    3.get_iplist(self,soup)：从BeautifulSoup对象获取代理ip信息
    4.get_ip_form(self,result=None)：从ip信息提取ip格式
    5.check_ip(self,test_url,ip_list=None,timeout=10):拿一个网站去检查ip是否可用
    6.get_ip_pool(self,test_url="https://music.163.com/",page_num = 4,timeout = 3)：获取ip池
    '''
    def __init__(self,ip_url_ls= 'http://www.xicidaili.com/nn/'):
        print("-----从西刺代理获取代理IP----------")
        self.ip_url_ls = ip_url_ls
    
    def check_chinese(self,check_str):
        '''
        功能
        ----
        检查ip号是否还有中文字符，如果有中文字符则去掉
        
        参数
        ----
        check_str:字符串，表示代理ip号
        
        返回
        ---
        返回True或者False
        '''
        zhPattern = re.compile(u'[\u4e00-\u9fa5]+')
        match = zhPattern.search(check_str)
        if match:
            return True
        else:
            return False
    
    def visit_url(self,ip_url,prox_ip=None):
        '''
        功能
        ------
        访问西刺代理网站，获取代理ip
        
        参数
        ------
        ip_url:字符串，爬取西刺代理url的初始入口
        prox_ip:列表，如["192.1681.1.1":“800”]
        
        返回值
        ------
        soup:BeautifulSoup对象，用来提取代理ip
        '''
        global headers
        headers={ "Accept": "application/json, text/javascript, */*; q=0.01",
         "Accept-Encoding": "gzip, deflate, br",
         "Accept-Language": "zh-CN,zh;q=0.8",
         "Connection": "keep-alive",
         "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
         'User-Agent':"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.103 Safari/537.36"}
        is_continue = True  #设置循环次数
        while is_continue:
            try:
                if prox_ip is None:
                    res = requests.get(ip_url,headers = headers)  #访问url，不设代理ip访问
                else:
                    http = prox_ip[0]   
                    ip = http+"://"+prox_ip[1]
                    proxies={http:ip}
                    res = requests.get(self.ip_url,headers = headers,proxies = proxies) #设代理ip访问
                html =  res.content.decode('utf-8')
                soup  =  BeautifulSoup(html,'lxml')
                is_continue = False 
            
            except HTTPError as e:
                print("---断网---")
                time.sleep(2)

            except Timeout as e:
                print("---请求超时---")
                time.sleep(2)

            except ConnectionError as e:
                print("---访问被拒---")
                is_continue = True
                time.sleep(2)

        return soup


    #*******获取ip信息**********
    def get_iplist(self,soup):

        '''
        功能：对解析后的网页进行清洗，获得目标变量

        参数
        ----
        soup：BeautifulSoup对象，网页元素经过解析后的对象，包含了ip、端口号以及其他信息。

        返回值
        -----
        result:数组，装载了清洗得到的目标内容，如何ip、端口号以及其他信息
        '''
        result = []
        for i in soup.select("#ip_list .odd"):  #遍历每一组信息
            string = ""                         #初始化空字符
            for j in i.select("td"):           #信息存在td标签的text中
                if j.text.strip()!='':         #过滤掉没有text的td标签
                    info = j.text.strip()      #去除两边的空字符
                    string = string + info + "|"

            for m in i.select(".bar"):      #反应速度和连接时长都在此处
                time = m["title"]           #反应时间和连接时间
                string = string+time+"|"    #
            result.append(string)           #保存每一组的string
        return result

    def get_ip_form(self,result=None):
        '''
        功能：对获取的ip信息进行整合成符合requests的形式

        参数
        ----
        result：数组，装载了清洗得到的目标内容，如何ip、端口号以及其他信息

        返回值
        -----
        ip_list:数组，获取新的ip组

        '''
        ip_list = []                  #用来装整合的ip
        for i in result:              #遍历每一条ip信息
            if 'sock' not in i:       #删选socket类的代理ip
                a = i.split("|")      #分割
                type1 = a[4].lower() #将代理ip的类型全部变成小写
                ip = a[0]            #ip号
                port=a[1]            #代理ip端口
                ip_list.append({type1:type1+"://"+ip+":"+port}) #添加整合好的ip记录
        return ip_list

    def check_ip(self,test_url,ip_list=None,timeout=10):
        '''
        功能：对每一个ip进行测试，返回有效的，提除无效的

        参数
        ----
        ip_list：数组，装载代理ip的类型，代理ip和端口
        url：字符串，用来检测ip是否可用的url
        timeout:整型，访问时间上限，如果超过该时间限制仍访问不成功，即报错。

        返回值
        -----
        new_ip_list:数组，获取新的ip组

        '''
        new_ip_list = [] 
        for i in ip_list:
            try:
                if '天' not in list(i.values())[0] and not self.check_chinese(list(i.values())[0]):
                    res = requests.get(test_url,proxies=i,timeout=timeout,headers=headers)
                if res.status_code == 200:
                    new_ip_list.append(i)

            except Exception as e:
                pass

            except KeyboardInterrupt:
                return new_ip_list
        return new_ip_list
    

    def get_ip_pool(self,test_url="https://music.163.com/",page_num = 4,timeout = 3):
        '''
        功能：获取代理ip网站的ip列表，同时对指定的网站进行测试
        
        参数
        ------
        test_url:字符串，表示的是测试ip能否访问的网站，默认为网易云音乐的官方网站。
        
        timeout:数值型，最大采取时间。
        
        page_num:int型，爬取西刺网最多的页面数。
        
        返回值
        -------
        new_ip_pool:列表，返回经过检查后的ip列表
        '''
        ip_pool = []
        #**********获取西刺代理的ip，请检验*******************
        for num in range(1,page_num+1):
            ip_url = self.ip_url_ls + str(num)
            print("正在爬取{0}".format(ip_url))
            soup = self.visit_url(ip_url)   ##访问西刺网
            result = self.get_iplist(soup)  #获取第一页的ip结果
            ip_list = self.get_ip_form(result=result) #获取ip形式
            print("正在测试ip能否访问{0}".format(test_url))
            new_ip_list = self.check_ip(test_url,ip_list,timeout) #检查ip
            ip_pool.extend(new_ip_list)
    
        #*******对ip池进行去重*******************
        new_ip_pool = []
        for i in ip_pool:
            if i not in new_ip_pool:
                new_ip_pool.append(i)
        print("一共获取了{0}个ip".format(len(new_ip_pool)))
        return new_ip_pool


# In[229]:

new_ip_pool = Ip_pool().get_ip_pool(page_num=1)


# ### 继承

# In[231]:

class Crawl_common(object):
    '''
    这是用来爬取大众点评的共有包，包含了以下的函数。
    
    函数
    -------
    
    1. requests_visit_url(self,url,is_use_ip =False,timeout=3)
        函数功能：访问特定的url，带有ip池的功能
        当is_use_ip等于False时，即不用代理ip池去访问，如果is_use_ip等于True时，即使用代理池去访问
          
        
    '''
    def __init__(self,test_url = 'https://music.163.com/',page_num=3,timeout=3):
        '''
        功能：生成ip池
        
        参数
        ----
        test_url:字符串，检测代理ip池是否正常工作的网址
        page_num:整数型，获取西刺代理的
        '''
        self.test_url = test_url
        self.page_num = page_num
        self.timeout = timeout
        global ip_pool
        global bad_ip
        
        #获取代理ip池
        ip_pool= Ip_pool().get_ip_pool(self.test_url,page_num=self.page_num,timeout=self.timeout)
        print("-----------ip池已经获取完毕---------------------")
    
    #*************带ip池访问url**********************************
    def requests_visit_url(self,url,is_use_ip =True,timeout=5):
        '''
        功能：自带ip池功能来放访问特定的url
        
        参数
        ----
        url：sring，表示特定的ul
        is_use_ip :bool，True表示采用ip池访问
        timeout:int,表示一次访问url的最大超时限制
        
        结果
        ----
        soup:BeautifulSoup对象，可以用来解析网页
        '''
        global ip_pool
        global bad_ip
        headers = {"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/61.0.3163.100 Chrome/61.0.3163.100 Safari/537.36"}
        bad_ip = []  #用来装坏的ip
        
        #*********如果不设置ip的话**********************************
        if is_use_ip == False:
            res = requests.get(url,headers = headers,timeout=timeout)  #访问url，不设代理ip访问
            html =  res.content.decode('utf-8')
            soup  =  BeautifulSoup(html,'lxml')
            if soup.title.text == '403 Forbidden' or "有道" in soup.title.text:
                print("ip被禁止了！！！！！！！！！！！！！！！！")
                raise ConnectionError
           
        #************如果设置ip的话，则执行这一段*********************
        else:
            is_continue = True   #设置循环标志
            while is_continue:
            #整理成ip地址的格式
                try:
                    #如果无效的ip等于整个ip池的ip个数时，重新再爬一次
                    if len(ip_pool)==len(bad_ip):
                        ip_url = 'http://www.xicidaili.com/nn/'
                        ip_pool= Ip_pool().get_ip_pool(self.test_url,timeout=2,page_num=3)
                        proxies = random.choice(ip_pool)
                        bad_ip = []
                    #******随机生成一个ip*******
                    proxies = random.choice(ip_pool)
                    
                    #*******用代理ip访问********
                    res = requests.get(url,headers = headers,proxies = proxies,timeout=timeout) #设代理ip访问
                    html =  res.content.decode('utf-8')
                    soup  =  BeautifulSoup(html,'lxml')
                
                    #********如果返回网页被禁止的情况，触发异常,否则返回正常**********
                    if  soup.title.text == '403 Forbidden' or "有道" in soup.title.text:
                        print("ip被禁止了!!!!!!!!!!!!!!!!!!!!")
                        raise ConnectionError
                    else:
                        is_continue = False

                except HTTPError as e:
                    bad_ip.append(proxies)
                    print("断网")
                    proxies = random.choice(ip_pool)
                    time.sleep(2)


                except Timeout as e:
                    bad_ip.append(proxies)
                    print("超时")
                    proxies = random.choice(ip_pool)
                    time.sleep(2)


                except ConnectionError as e:
                    bad_ip.append(proxies)
                    print("访问被拒")
                    proxies = random.choice(ip_pool)
                    time.sleep(2)
                    
                except AttributeError as e:
                    bad_ip.append(prox_ip)
                    print("----------")
                    proxies = random.choice(ip_pool)
                    time.sleep(2)
                    
                except ChunkedEncodingError as e:
                    bad_ip.append(proxies)
                    print("ChunkedEncodingError")
                    proxies = random.choice(ip_pool)
                    time.sleep(2)

        return soup


# In[ ]:



