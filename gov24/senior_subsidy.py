from datetime import datetime
import requests
import time
import os
import copy

from bs4 import BeautifulSoup
import pandas as pd
from common import post_processing_text, post_processing_apply_content
from common import convert_list_to_multiline, apply_text_wrap_and_adjust


def crawl_subsidy():
    subsidy_list = []
    subsidy = {
        '제목': None,
        '내용': None,
        '소관기관': None,
        '신청기간': None,
        '전화문의': None,
        '신청방법': None,
        '접수기관': None,
        '지원형태': None,
        '지원대상': None,
        '지원내용': None,
        'url': None,
    }
    url = "https://www.gov.kr"  # 메인 페이지 URL로 시작
    base_path = "/search?srhQuery=노인&collectionCd=rcv&textAnalyQuery=&policyType=&webappType=&realQuery=노인&pageSize=10&publishOrg=&sfield=&recommendpageIndex=1&sort=RANK&condSelTxt=&reSrchQuery=&sortSel=RANK&pageIndex="
    page_index = 1
    content_index = 1

    while True:
        search_path = base_path + str(page_index)
        response = requests.get(url + search_path)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        results = soup.find('div', class_='result_cont_list')

        if not results:
            print('All crawling is done!')
            break

        li_tag = results.find_all('li', class_='result_li_box')

        for li in li_tag:
            print(f"{content_index}. Processing ...")
            subsidy_dict = copy.deepcopy(subsidy)
            subsidy_dict['제목'] = li.find('a').text
            subsidy_dict['url'] = url + li.find('a')['href']
            subsidy_dict['내용'] = post_processing_text(li.find('p', class_='list_info_txt').text.replace('○', ''))
            subsidy_dict['소관기관'] = post_processing_text(li.find('div', class_='badge_box').text.replace('보조금24', ''))
            response = requests.get(subsidy_dict['url'])
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            panel_1 = soup.find('div', id='panel1')
            panel_1_list = ['term', 'call', 'method', 'reception', 'support']
            subsidy_dict_title = ['신청기간', '전화문의', '신청방법', '접수기관', '지원형태']

            for i in range(len(panel_1_list)):
                if panel_1.find('li', class_=panel_1_list[i]):
                    if panel_1_list[i] == 'method':
                        subsidy_dict[subsidy_dict_title[i]] = post_processing_apply_content(panel_1.find('li', class_=panel_1_list[i]).find('span').text)
                    else:
                        subsidy_dict[subsidy_dict_title[i]] = post_processing_text(panel_1.find('li', class_=panel_1_list[i]).find('span').text)

            response = requests.get(subsidy_dict['url'])

            subsidy_list.append(subsidy_dict)

            panel_2 = soup.find('div', id='panel2').find('h2', class_='blind').find_next('pre').text
            subsidy_dict['지원대상'] = post_processing_apply_content(post_processing_text(panel_2))

            panel_3 = soup.find('div', id='panel3').find('h2', class_='blind').find_next('pre').text
            subsidy_dict['지원내용'] = post_processing_apply_content(post_processing_text(panel_3))

            content_index += 1
        print(f"Crawling is done!: page {page_index}")
        page_index += 1
    
    generate_excel(subsidy_list)

def generate_excel(first_form):
    # 현재 날짜를 기준으로 파일 경로 생성
    now = datetime.now().strftime('%Y%m%d')
    output_dir = 'senior_generate_excel'
    os.makedirs(output_dir, exist_ok=True)  # 디렉토리 생성
    output_path = f'{output_dir}/{now}_정부24_시니어_보조금24.xlsx'

    # 각 데이터의 리스트 항목을 변환
    first_form = [{k: convert_list_to_multiline(v) for k, v in item.items()} for item in first_form]

    # ExcelWriter를 사용하여 여러 시트를 작성
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # 첫 번째 폼 저장
        df1 = pd.DataFrame(first_form)
        df1.to_excel(writer, index=False, sheet_name='form1')

    # 텍스트 줄 바꿈, 셀 높이 조정 및 위쪽 정렬 적용
    apply_text_wrap_and_adjust(output_path, ['form1'])

    print(f"Excel file has been saved to {output_path}")


if __name__ == '__main__':
    crawl_subsidy()
