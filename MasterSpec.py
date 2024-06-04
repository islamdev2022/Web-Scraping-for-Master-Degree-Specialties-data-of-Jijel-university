import requests
from bs4 import BeautifulSoup
import json

# Global dictionary to store the accumulated data
data_structure = {}

def fetch_page(url):
    """ Fetch the content of a page """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Will raise an HTTPError for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_links(html):
    """ Extract links from HTML content within the categories """
    soup = BeautifulSoup(html, 'html.parser')
    categories = soup.find_all('div', class_='category')  # Look for divs that are marked as category
    return [cat.find('a')['href'] for cat in categories if cat.find('a')]

def scrape_information(url, specialty, semester):
    """ Scrape the course and teacher names from the final page """
    html = fetch_page(url)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        course_boxes = soup.find_all('div', class_='coursebox')
        courses = []
        for box in course_boxes:
            course_name = box.find('h3', class_='coursename').a.get_text(strip=True)
            teacher_name = "No teacher information available"
            summary_div = box.find('div', class_='summary')
            if summary_div:
                teacher_paragraph = summary_div.find('p')
                if teacher_paragraph:
                    # Clean the text to just get the teacher's name
                    teacher_name = teacher_paragraph.get_text(strip=True)
                    teacher_name = teacher_name.replace("L'Enseignant:", "").replace("L'enseignant:", "").strip()
            
            # If no 'p' tag with teacher info, look for 'ul' with class 'teachers'
            if not summary_div or not teacher_paragraph:
                teacher_list = box.find('ul', class_='teachers')
                if teacher_list:
                    teacher_link = teacher_list.find('a')
                    if teacher_link:
                        teacher_name = teacher_link.get_text(strip=True)
            courses.append({"Course": course_name, "Teacher": teacher_name})
            print(f"Course: {course_name}, Teacher: {teacher_name}")
        
        # Save data into the global structure
        if specialty not in data_structure:
            data_structure[specialty] = {}
        data_structure[specialty][semester] = courses
        print(f"Specialty: {specialty}, Semester: {semester}")

def navigate_links(url, depth, specialty=None, semester=None):
    """ Navigate through levels of links before scraping information """
    if depth == 0:
        scrape_information(url, specialty, semester)
    else:
        html = fetch_page(url)
        if html:
            links = extract_links(html)
            for link in links:
                nav_html = fetch_page(link)
                if nav_html:
                    soup = BeautifulSoup(nav_html, 'html.parser')
                    nav = soup.find('ol', class_='breadcrumb')
                    if nav:
                        current_specialty = nav.find_all('li')[-2].get_text(strip=True)
                        current_semester = nav.find('span').get_text(strip=True)
                        navigate_links(link, depth - 1, current_specialty, current_semester)

def save_data():
    """ Save the accumulated data to a JSON file """
    with open('spec_master.json', 'w', encoding='utf-8') as file:
        json.dump(data_structure, file, indent=4,ensure_ascii=False)

# Starting URL
start_url = 'http://elearning.univ-jijel.dz/course/index.php?categoryid=637'
depth_of_navigation = 2  # Adjust based on the depth of links you want to follow
navigate_links(start_url, depth_of_navigation)
save_data()  # Save all data after navigation is complete
