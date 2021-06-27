import selenium
from selenium import webdriver
from selenium.webdriver import ActionChains

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager # setting up the chromedriver automatically using webdriver_manager

import requests
from bs4 import BeautifulSoup
from html_table_parser import parser_functions
import urllib.request

from sqlalchemy import create_engine
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb

import sys
import os
from tqdm import tqdm
import time

import pandas as pd

# 초기자료

columns_name=['관측일','평균기온(℃)', '최저기온(℃)','최고기온(℃)','평균풍속(m/s)','최대풍속(m/s)','상대습도평균(%)','상대습도최소(%)',
        '증발량소형(mm)','증발량대형(mm)','평균운량(1/10)','해면기압(h㎩)','최심적설(㎝)','이슬점온도(℃)',
        '최대풍향','일사량(mj/㎡)','일조시간']

calender=[(0,0), (5,1), (4,1), (2,4), (5,1), (5,1), (1,3), (5,1), (5,1),
          (1,1), (0,0), (5,1), (5,1), (1,2),(5,1), (1,3),(1,4),
          (2,5), (5,1), (5,1), (5,1), (4,4), (4,4), (5,7), (5,1)]
engine = create_engine("mysql+mysqldb://root:"+"0000"+"@localhost/weather", encoding='utf-8')
conn = engine.connect()

# Selenium 설정
options = webdriver.ChromeOptions()
options.add_argument('window-size=1920,1080')

driver_path=os.getcwd()+'\chromedriver.exe'
driver = webdriver.Chrome(driver_path, options=options) #ChromeDriverManager().install()

url = "http://www.wamis.go.kr/wkw/we_dwtwtobs.do"
driver.get(url)
driver.implicitly_wait(3)

## 일자료로 바꿔주기
path='//*[@id="select3"]'
category = driver.find_element_by_xpath(path)
category.click()


#driver.back()
for block in range(15,20): #한강 대권역
    #block=19
    if block==22:
        continue
    if block==16:
        continue
    if block==18:
        continue
    # 10131093의 경우 결과가 없기 때문에 예외처리
    if block==10:
        continue
    row, col=calender[block]
    df1=pd.DataFrame(columns=columns_name)
    
        ## 각 관측소 코드 저장
    name_path='//*[@id="grdResult"]/tr['+str(block)+']/td[6]'
    
    code_name=driver.find_element_by_xpath(name_path).text
    print("######","block :", block, "code_name :", code_name, "######")
    
    ## 각 관측소 조회 클릭
    path='//*[@id="grdResult"]/tr['+str(block)+']/td[2]'
    category=driver.find_element_by_xpath(path)
    category.click()
    driver.implicitly_wait(3)
    count=0
    time.sleep(3)
   
    # 관측소에 대한 정보 수집 시도
    try:    
        while True:
            if count==0:
                print("처음 시작날짜 :", count)
                ## 관측기간 시작날짜 박스 선택
                path='//*[@id="dtpictext"]'
                category=driver.find_element_by_xpath(path)
                category.click()

                ## 관측기간 년도 박스 클릭
                path='//*[@id="ui-datepicker-div"]/div[1]/div/select'
                category=driver.find_element_by_xpath(path)
                category.click()
                driver.implicitly_wait(1)
                
                ## 관측기간 첫번째 년도 옵션 클릭
                path='//*[@id="ui-datepicker-div"]/div[1]/div/select/option[1]'
                category=driver.find_element_by_xpath(path)
                category.click()

                ## 처음 시작날짜 선택
                path='//*[@id="ui-datepicker-div"]/table/tbody/tr['+str(row)+']/td['+str(col)+']'
                category=driver.find_element_by_xpath(path)
                category.click()
                start_date=category.get_attribute('outerHTML')
                driver.implicitly_wait(3)

                start_date=list(start_date)
                start_date_text=""
                for i in start_date:
                    if i.isdigit():
                        start_date_text+=i
                # 예시 : 8200828
                start_month=int(start_date_text[0])
                start_year=int(start_date_text[1:5])
            else:
                
                ## 관측기간 시작날짜 박스 선택
                path='//*[@id="dtpictext"]'
                category=driver.find_element_by_xpath(path)
                category.click()

                ## 관측기간 년도 박스 클릭
                path='//*[@id="ui-datepicker-div"]/div[1]/div/select'
                category=driver.find_element_by_xpath(path)
                category.click()
                driver.implicitly_wait(1)
            
                ## 관측기간 년도 옵션 클릭(종료된 날짜와 같게)
                path='//*[@id="ui-datepicker-div"]/div[1]/div/select/option['+str(count+1)+']'
                category=driver.find_element_by_xpath(path)
                category.click()

                if count==1:
                    print("년도 :", start_year+count)
                    ## 시작날짜를 모두 2월로 맞춰줌
                    if start_month>1:
                        for _ in range(start_month-1):
                            path='//*[@id="ui-datepicker-div"]/div[1]/a[1]' #왼쪽 버튼
                            category=driver.find_element_by_xpath(path)
                            category.click()
                            driver.implicitly_wait(1)
                    elif start_month<1:
                        for _ in range(1-start_month):
                            path='//*[@id="ui-datepicker-div"]/div[1]/a[2]' #오른쪽 버튼
                            category=driver.find_element_by_xpath(path)
                            category.click()
                            driver.implicitly_wait(1)
                    else: # start_month==1(2월일 때)
                        pass
                    
                    ## 시작날짜 선택
                    path='//*[@id="ui-datepicker-div"]/table/tbody/tr[2]/td[1]' # [1][7]을 종료날짜로 맞췄으므로
                    category=driver.find_element_by_xpath(path)
                    category.click()    
                    driver.implicitly_wait(3)
                    
                else:
                    print("년도 :", start_year+count)
                    ## 세 번째 이후 시작날짜 선택
                    
                    ## 시작날짜 선택
                    path='//*[@id="ui-datepicker-div"]/table/tbody/tr[2]/td[1]' # [1][7]을 종료날짜로 맞췄으므로
                    category=driver.find_element_by_xpath(path)
                    category.click()
                    driver.implicitly_wait(3)
            
            time.sleep(5)
            ##########################################################

            ## 관측기간 종료날짜 박스 선택
            path='//*[@id="dtpictext2"]'
            category=driver.find_element_by_xpath(path)
            category.click()

            ## 관측기간 년도 박스 클릭
            path='//*[@id="ui-datepicker-div"]/div[1]/div/select'
            category=driver.find_element_by_xpath(path)
            category.click()
            driver.implicitly_wait(1)

            time.sleep(3)
            ## 관측기간 년도 옵션 클릭
            count+=1 #내년 2월을 선택
            path='//*[@id="ui-datepicker-div"]/div[1]/div/select/option['+str(count+1)+']'
            category=driver.find_element_by_xpath(path)
            category.click()
            time.sleep(3)

            if  count<(2021-start_year):
                print("종료날짜 : ", start_year+count)
                ## 종료날짜 선택(시작날짜+1년-02-첫째주 마지막날짜)
                path='//*[@id="ui-datepicker-div"]/table/tbody/tr[1]/td[7]'
                category=driver.find_element_by_xpath(path)
                category.click()
                driver.implicitly_wait(3)
                time.sleep(3)
            else: #count==(2021-start_year)
                print("종료날짜 : ", start_year+count)
                ## 2021년도 종료날짜 선택
                path='//*[@id="ui-datepicker-div"]/table/tbody/tr[3]/td[1]'
                category=driver.find_element_by_xpath(path)
                category.click()
                driver.implicitly_wait(3)
                time.sleep(3)        
            
            if count==1:
                print("전체 선택 클릭 : ",count)
                ## 검색항목 전체선택 클릭(최초의 한 번만 해 주면 됨)
                path='//*[@id="btnSelectAll"]'
                category=driver.find_element_by_xpath(path)
                category.click()
                driver.implicitly_wait(3)
                time.sleep(3)

            ## 검색하기
            if (start_year+count)==2016:
                continue
            if block==20 and (start_year+count)==2012:
                continue
            if block==21 and (start_year+count)==2013:
                continue
            if block==23 and (start_year+count)==2013:
                continue
            if block==24 and (start_year+count)==2014:
                continue
            if block==15 and (start_year+count)==2011:
                continue
            if block==17 and (start_year+count)==2012:
                continue
            if block==19 and (start_year+count)==2012:
                continue
            if block==19 and (start_year+count)==2019:
                continue
            
            
            try:
                path='/html/body/div[7]/div/div[1]/dl[3]/dd/a'
                category=driver.find_element_by_xpath(path)
                category.click()
                print("검색하기 시작")
                driver.implicitly_wait(5)
                time.sleep(7+count)
                print("검색하기 끝")
                soup = BeautifulSoup(driver.page_source, "html.parser")
            except:
                driver.back()
                driver.implicitly_wait(5)
                driver.forward()
                driver.implicitly_wait(5)
                print("Error :", "시작날짜",count-1, "종료날짜",count)
                continue

            ## 표 가져오기
            #soup = BeautifulSoup(driver.page_source, "html.parser")
            print("soup")
            time.sleep(7+count)
            data=soup.find("table", {"class":"tb_base"})
            table=parser_functions.make2d(data)

            
            df2=pd.DataFrame(data=table[:], columns=columns_name)
            time.sleep(2)

            print(df2.shape)
            print("#############################")

            df1=pd.concat([df1, df2])
            time.sleep(3) 
                  
            if count==(2021-start_year):
                break
    
    except:
        print("Error :" , code_name)    
    # 이전 페이지로 가기(다음 관측소에 대한 정보를 얻기 위해)
    driver.back()
    time.sleep(5)
    if len(df1)!=0:
        # 관측소코드 추가해야 함
        df1['관측소코드']=code_name
        time.sleep(2)
        print(df1.shape)
        

        # 완성된 관측소 dataframe을 db에 저장
        df1.to_sql(name=code_name, con=engine, if_exists='replace')
        time.sleep(10)
    


## block 1, block 3 완성

