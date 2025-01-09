import requests
import time
import copy
import re
from bs4 import BeautifulSoup


def crawl_senior():
    first_form = []
    second_form = []
    third_form = []
    first_form_sheet = {
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
        'url': None,
    }
    second_form_sheet = {
        '제목': None,
        '신청방법': None,
        '신청자격': None,
        '처리기간': None,
        '신청서': None,
        '구비서류': None,
        '수수료': None,
        'url': None,
    }
    third_form_sheet = {
        '제목': None,
        '신청방법': None,
        '신청자격': None,
        '처리기간': None,
        '신청서': None,
        '구비서류': None,
        '수수료': None,
        'url': None,
    }
    # 대상 URL
    url = "https://www.gov.kr"  # 메인 페이지 URL로 시작
    base_path = "/search?srhQuery=노인&collectionCd=service&textAnalyQuery=&policyType=&webappType=&realQuery=노인&pageSize=10&publishOrg=&sfield=&sort=RANK&condSelTxt=&reSrchQuery=&sortSel=RANK&pageIndex="
    page_index = 1
    content_index = 1

    while True:
        # 요청할 URL 생성
        search_path = base_path + str(page_index)
        response = requests.get(url + search_path)
        response.raise_for_status()

        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # 크롤링할 데이터 추출
        results = soup.find('div', class_='result_cont_list')

        if page_index > 3:
            break
        # if not results:
        #     print('All crawling is done!')
        #     break

        li_tag = results.find_all('li', class_='result_li_box')
        for li in li_tag:
            url_tag = li.find('a', class_='list_font17', href=True)
            connect_url = requests.get(url + url_tag['href'])
            connect_url.raise_for_status()
            connect_soup = BeautifulSoup(connect_url.text, 'html.parser')

            first_form_class = 'contents layer'
            second_form_class = 'contentsWrap mw_wrap'
            third_form_class = 'cont-inner info-detail'

            contents = connect_soup.find('div', class_=first_form_class)

            # 폼 클래스와 처리 로직을 매핑
            form_classes = [
                (first_form_class, "form1", process_form_1, first_form, first_form_sheet),
                (second_form_class, "form2", process_form_2, second_form, second_form_sheet),
                (third_form_class, "form3", process_form_3, third_form, third_form_sheet),
            ]

            contents = None

            for idx, (form_class, form_name, process_func, form_list, form_sheet) in enumerate(form_classes):
                contents = connect_soup.find('div', class_=form_class)
                if contents:
                    print(f"{content_index}. Processing {form_name} ...")
                    if process_func:  # 처리 함수가 있는 경우 실행
                        processed_data = process_func(form_sheet, connect_soup)
                        processed_data['url'] = url + url_tag['href']
                        form_list.append(processed_data)
                    break

            # 처리할 폼을 찾지 못한 경우
            if contents is None:
                print("This is a new form. Since it cannot be processed, move on to the next step.")


            # 처리할 폼을 찾지 못한 경우
            if contents is None:
                print("This is a new form. Since it cannot be processed, move on to the next step.")

            content_index += 1
        print(f"Crawling is done!: page {page_index}")
        page_index += 1

    return(third_form)


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

def post_processing_text(content):
    return re.sub(r'[\r\n\t ]', '', content).strip()

def process_form_1(first_form_sheet, connect_soup):
    ffs = copy.deepcopy(first_form_sheet)  # 딕셔너리 복사
    title  = connect_soup.find('div', id='pageCont').find('h2').text  # 제목
    if title:
        ffs['제목'] = title
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
                ffs[apply_title] = post_processing_apply_type(apply_type)
            else:
                print(f'{title} section 1: error!, error!')

    # section 3: 지원대상
    # cont_box_list_1 = cont_box_list[1].find_all('li')
    apply_people_tag = cont_box_list[1].find('div', class_='tx')
    if apply_people_tag:
        apply_people = decode_html(apply_people_tag)
        ffs['지원대상'] = post_processing_apply_content(apply_people)
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
            ffs[used_title.text] = post_processing_apply_content(used_content)
        else:
            print(f'{title} section 4 {used_title.text}: error!, error!')

    # section 5: 근거법령 :: 소정기관 :: 최종수정일
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
                ffs[ref_title.text] = html_to_dictList(ref_content_result)
            else:
                ffs[ref_title.text] = ref_content_result
        else:
            print(f'{title} section 5 {ref_title.text}: error!, error!')

    return ffs

def process_form_2(second_form_sheet, connect_soup):
    sfs = copy.deepcopy(second_form_sheet)
    # 제목
    title = connect_soup.find('div', class_='title', id='pageCont').find('h2').text
    sfs['제목'] = title

    # wrap_col
    wrap_col = connect_soup.find('div', class_='wrap_col')

    # 서비스 개요
    service_info = wrap_col.find('div', class_='info_svc_list').find_all('li')
    for i in range(len(service_info)):
        info_title = service_info[i].find('p', class_='tit').text
        sfs[info_title] = post_processing_text(service_info[i].find('p', class_='txt').text)

    return sfs

def process_form_3(third_form_sheet, connect_soup):
    tfs = copy.deepcopy(third_form_sheet)
    tfs['제목'] = post_processing_text(connect_soup.find('h2').text)

    return tfs

print(crawl_senior())


# excel로 출력하는 기능 추가 (sheet별로)
# form_3 테이블 정보 가져오기
