import requests
import time
import copy
import re
from bs4 import BeautifulSoup


def crawl_senior():
    first_form = []
    issue_list = []
    content_excel_sheet = {
        '제목': None,
        '지원형태': None,
        '지원내용': None,
        '지원대상': None,
        '신청기한': None,
        '절차/방법': None,
        '구비서류': None,
        '접수기관': None,
        '근거법령': None,
        '소관기관': None,
        '최종수정일': None,
    }
    issue_excel_sheet = {}
    # 대상 URL
    url = "https://www.gov.kr"  # 메인 페이지 URL로 시작
    base_path = "/search?srhQuery=노인&collectionCd=service&textAnalyQuery=&policyType=&webappType=&realQuery=노인&pageSize=10&publishOrg=&sfield=&sort=RANK&condSelTxt=&reSrchQuery=&sortSel=RANK&pageIndex="
    page_index = 1

    while True:

        # 요청할 URL 생성
        search_path = base_path + str(page_index)
        response = requests.get(url + search_path)
        response.raise_for_status()

        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # 크롤링할 데이터 추출
        results = soup.find('div', class_='result_cont_list')
        if not results:
            print('All crawling is done!')
            break

        li_tag = results.find_all('li', class_='result_li_box')
        for li in li_tag:
            url_tag = li.find('a', class_='list_font17', href=True)
            connect_url = requests.get(url + url_tag['href'])
            connect_url.raise_for_status()
            connect_soup = BeautifulSoup(connect_url.text, 'html.parser')

            content_btn_class = 'contents layer'
            issue_btn_class = 'contentsWrap mw_wrap'

            contents = connect_soup.find('div', class_=content_btn_class)
            # 발급하기 버튼 유형
            if contents is None:
                contents = connect_soup.find('div', class_=issue_btn_class)
            # 내용보기 버튼 유형
            else:
                ces = copy.deepcopy(content_excel_sheet)  # 딕셔너리 복사
                title  = connect_soup.find('div', id='pageCont').find('h2').text  # 제목
                if title:
                    ces['제목'] = title
                else:
                    print(f'{title} title: error!, error!')

                # section 1: 지원형태
                cont_box_list = connect_soup.find_all('ul', class_='cont-box-lst')
                cont_box_list_0 = cont_box_list[0].find_all('li')
                for i in range(len(cont_box_list_0)):
                    apply_title = cont_box_list_0[i].find('p', class_='tt').text
                    if apply_title:
                        apply_type_tag = cont_box_list_0[0].find('div', class_='tx')
                        if apply_type_tag:
                            apply_type = decode_html(apply_type_tag)
                            ces[apply_title] = post_processing_apply_type(apply_type)
                        else:
                            print(f'{title} section 1: error!, error!')

                # section 3: 지원대상
                # cont_box_list_1 = cont_box_list[1].find_all('li')
                apply_people_tag = cont_box_list[1].find('div', class_='tx')
                if apply_people_tag:
                    apply_people = decode_html(apply_people_tag)
                    ces['지원대상'] = post_processing_apply_content(apply_people)
                else:
                    print(f'{title} section 3: error!, error!')

                # section 4: 절차/방법 :: 신청기한 :: 구비서류 :: 접수기관
                cont_box_list_2 = cont_box_list[2].find_all('li')
                for i in range(len(cont_box_list_2)):
                    used_title = cont_box_list_2[i].find('p', class_='tt')
                    if not used_title:
                        continue
                    used_content_tag = cont_box_list_2[i].find('div', class_='tx')
                    if used_content_tag:
                        used_content = decode_html(used_content_tag)
                        ces[used_title.text] = post_processing_apply_content(used_content)
                    else:
                        print(f'{title} section 4 {used_title.text}: error!, error!')

                # section 5: 근거법령, 소정기관, 최종수정일
                cont_box_list_3 = cont_box_list[3].find_all('li')
                for i in range(len(cont_box_list_3)):
                    ref_title = cont_box_list_3[i].find('p', class_='tt')
                    if not ref_title:
                        continue
                    ref_content_tag = cont_box_list_3[i].find('div', class_='tx')
                    if ref_content_tag:
                        ref_content = decode_html(ref_content_tag)
                        ref_content_result = post_processing_apply_content(ref_content)
                        if ref_title.text == '근거법령':
                            ces[ref_title.text] = html_to_dictList(ref_content_result)
                        else:
                            ces[ref_title.text] = ref_content_result
                    else:
                        print(f'{title} section 5 {ref_title.text}: error!, error!')

                # 리스트에 추가    
                first_form.append(ces)
        print(f"Crawling is done!: page {page_index}")
        page_index += 1

    print(len(first_form))
    print(first_form)
    return(first_form)


def decode_html(html_tag):
    raw_html = html_tag.decode_contents()
    return raw_html.replace('<br/>', '').replace('</br>', '').replace('<br>', '').replace('&nbsp;', '').strip()

def post_processing_apply_type(apply_type):
    cleaned_list = [item.strip() for item in apply_type.split() if item.strip()]
    result = ", ".join(cleaned_list)
    return result

def post_processing_apply_content(apply_content):
    form_data = []
    cleaned_list = [item.strip() for item in apply_content.split() if item.strip()]
    original_string = " ".join(cleaned_list)
    split_result = re.split(r'(○ |- )', original_string)
    final_result = []
    temp = ""
    for part in split_result:
        if re.match(r'(○ |- )', part):  # 구분자인 경우
            if temp:  # temp에 기존 값이 있다면 추가
                final_result.append(temp.strip())
            temp = part  # 구분자로 초기화
        else:
            temp += part  # 기존 temp에 누적

    if temp:  # 마지막 부분 추가
        final_result.append(temp.strip())
    for split in final_result:
        if split != '':
            form_data.append(split.strip())
    return form_data

def html_to_dictList(html_list):
    html_content = ''.join(html_list)
    soup = BeautifulSoup(html_content, 'html.parser')
    result = []

    # 모든 <a> 태그를 찾기
    for a_tag in soup.find_all('a', class_='law'):
        # [법령] 텍스트와 href 값 추출
        text = a_tag.text.strip()
        href = a_tag['href'] if 'href' in a_tag.attrs else None
        # 딕셔너리 형태로 추가
        result.append({text: href})

    return result

crawl_senior()

# 발급하기 버튼 유형 기능 추가
# excel로 출력하는 기능 추가
# 양을 미리 측정해서 얼마나 남았는지 몇퍼센트 진행되었는지 표시하는 기능 추가
# 다른 양식 문제 해결 법 찾아야함
# 새로운 양식이나 오류 생기면 해당 제목만 가져오고 나머지 진행

# 양식 유형 더 조사해보기
