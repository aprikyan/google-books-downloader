import os
import urllib
import traceback
import regex as re
from time import sleep
from seleniumwire import webdriver
from progressbar import progressbar as bar
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

print("""
Google Books Downloader by @aprikyan, 2020.
 .   .   .   .   .   .   .   .   .   .   .
""")

def get_book_url():
    """
    Asks user for the URL, takes it,
    removes irrelevant suffixes, adds others,
    returns two URLs to extract data and links.
    """
    url = input("""
Step 1: Paste the URL of the book preview to be downloaded.
(e.g. https://books.google.com/books?id=buc0AAAAMAAJ&printsec=frontcover&sa=X&ved=2ahUKEwj-y8T4r5vrAhWKLewKHaIQBnYQ6AEwAXoECAQQAg#v=onepage&f=false)

Your input: """)
    
    try:
        id_part = re.findall(r"id=[A-Za-z0-9]+", url)[-1]
    except:
        print("Invalid input. Please try again.")
        get_book_url()
        
    return (f"https://books.google.com/books?{id_part}&pg=1&hl=en#v=onepage&q&f=false",
            f"https://books.google.com/books?{id_part}&pg=1&hl=en&f=false&output=embed&source=gbs_embed")

def get_book_data(url):
    """
    Inspects the opened book, returns a
    `str` with its title and author.
    """
    driver.get(url)
    driver.refresh()
    sleep(5)
    title = driver.find_element_by_class_name("gb-volume-title").text
    author = driver.find_element_by_class_name("addmd").text
    
    return f"{title} ({author})"

def capture_requests(url):
    """
    Scrolls through the whole book,
    returns the requests driver made.
    """
    driver.get(url)
    driver.refresh()
    sleep(5)
    checkpoint = ""
    
    while checkpoint != driver.find_element_by_class_name("pageImageDisplay"):
        checkpoint = driver.find_element_by_class_name("pageImageDisplay")
        checkpoint.click()
        # scrolling ~25 pages
        for i in range(25):
            html = driver.find_element_by_tag_name("body")
            html.click()
            for j in range(50):
                html.send_keys(Keys.DOWN)

    return str(driver.requests)

def extract_urls(requests):
    """
    Takes driver's requests as an input,
    returns a `dict` of page image URLs.
    """
    urls = re.findall(r"url='(https:\/\/[^']+content[^']+pg=[A-Z]+([0-9]+)[^']+)(&w=[0-9]+)'", requests)

    return {int(url[1]): url[0] + "&w=69420" for url in urls}

def save_backup():
    """
    Asks user whether to backup the available
    image URLs for later use. Does so, if yes.
    """
    save = input("""
Would you like to save a backup file (type Yes or No)?
Your input: """).upper()
    
    if save == "YES":
        with open(f"Backup of {book_data}.txt", "w") as f:
            f.write(str(all_pages))
        print(f"Succesfully backed up the book in {book_data}.txt!")
        
    elif save != "NO":
        print("Invalid input. Please try again.")
        save_backup()

def select_pages(user_input, all_pages):
    """
    Takes the range of pages user specified
    and image URLs of all pages available,
    returns a `dict` with selected pages only.
    """
    ranges = user_input.replace(" ", "").split(",")
    page_numbers = []
    
    if "all" in ranges:
        return all_pages
    while "odd" in ranges:
        page_numbers.extend([i for i in all_pages.items() if i[0] % 2])
        ranges.remove("odd")
    while "even" in ranges:
        page_numbers.extend([i for i in all_pages.items() if i[0] % 2 == 0])
        ranges.remove("even")
    for segment in ranges:
        if "-" in segment:
            a, b = segment.split("-")
            page_numbers.extend([i for i in all_pages.items() if int(a) <= i[0] <= int(b)])
        elif int(segment) in all_pages.keys():
            page_numbers.append((int(segment), all_pages[int(segment)]))

    return dict(set(page_numbers))
    
def get_cookie(url):
    """
    Driver needs to behave like a real
    user to GET page images. This function
    returns a cookie to bribe Google with.
    """
    cookies = []
    driver.get(url)
    driver.refresh()
    
    for request in driver.requests:
        if request.headers:
            if "Cookie" in request.headers.keys():
                cookies.append(request.headers["Cookie"])

    return cookies[0]

def download_imgs(pages, cookie, directory):
    """
    Takes the `dict` of pages to download,
    the cookie to use and the directory
    to save to, and then does the magic.
    """
    proxy = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy)
    opener.addheaders = [("user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30"),
                        ("cookie", cookie)]
    urllib.request.install_opener(opener)
    
    for number, url in bar.progressbar(pages.items()):
        urllib.request.urlretrieve(url, os.path.join(directory, f"page{number}.png"))

def step1():
    global book_data, all_pages
    
    from_url = input("""
Would you like to download a book from URL? Type No if you have a backup, otherwise type Yes.

Your input: """).upper()
    
    if from_url == "YES":
        data_url, pages_url = get_book_url()
        book_data = get_book_data(data_url)
        print(f"\nWe will now process the pages of {book_data} one by one. Sit back and relax, as this may take some time, depending on the number of its pages.\n")
        reqs = capture_requests(pages_url)
        all_pages = extract_urls(reqs)
        print("""Now that most of the job is done (yahoo!), it is highly recommended to backup the current progress we have made, so as not to lose it if an error happens to be thrown afterward.
Also, if you would like to download another segment of this book later, the backup will be used then to save your precious time.""")
        save_backup()
        
    elif from_url == "NO":
        backup = input("""
Enter the location of the backup file.
(e.g. C:/Users/User/Downloads/Backup_of_booktitle.txt)

Your input: """)        
        
        try:
            book_data = os.path.basename(backup)[10:-4]
            all_pages = eval(open(backup).read())
        except:
            print("Invalid input. Please try again.")
            step1()
            
    else:
        print("Invalid input. Please try again.")
        step1()

def step2():
    global selected_pages, cookie
    
    selection = input("""
Step 2: Specify the pages to be downloaded. You may use the combinations of:
-   exact numbers (e.g. 5, 3, 16)
-   ranges (e.g. 11-13, 1-100)
-   keywords odd and/or even, to download odd or even pages respectively
-   keyword all, to download all pages available
-   commas to seperate the tokens
Your input may look like "1, 10-50, odd, 603".
Note that only pages available for preview will be downloaded.

Your input: """)
    
    try:
        selected_pages = select_pages(selection, all_pages)
        
    except:
        print("Invalid input. Please try again.")
        step2()

    # it's a surprise tool that will help us later
    cookie = get_cookie(list(all_pages.items())[0][1])

def step3():    
    main_directory = input("""
Step 3 (optional): Specify the location to download the book pages to (a new folder will be created in that directory).
ENTER to save them right here.

Your input: """)
    
    try:
        new_directory = os.path.join(main_directory, book_data)
        os.mkdir(new_directory)
    except:
        print("Invalid input. Please try again.")
        step3()
        
    print(f"\nWe will now download all {len(selected_pages)} pages you selected. This will take a minute or two.\n")
    download_imgs(selected_pages, cookie, new_directory)

if __name__ == "__main__":
    global driver
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_experimental_option("prefs", {"safebrowsing.enabled": True})
    driver = webdriver.Chrome("chromedriver.exe", options=chrome_options)
    
    try:
        step1()
        step2()
        step3()
        
    except Exception as e:
        with open("google-books-downloader crash.log", "w") as log:
            log.write(traceback.format_exc())
        print(f"""
Something went wrong :/

Please make sure that:
-   you are connected to the Internet
-   the book you are trying to download has preview
-   you entered a valid URL of a Google Books book
-   your inputs correspond the formatting
-   you have permission to save/create files in this and the download directories
    
If it still repeats and you think this is an error, please report it on github.com/aprikyan/google-books-downloader.
When reporting, do not forget to attach the following file to the issue:
    {os.path.join(os.getcwd(), "google-books-downloader crash.log")}
""")
        
    else:
        print(f"""
The selected pages were successfully downloaded into the "{book_data}" folder!

Note that for your convenience the pages are saved as images. If you would like to combine them in a PDF (or another format), it might be done using specialized websites and apps.""")
        
        # combining in PDF involves asking about its DPI, size, etc, and
        # it would take much time and RAM, so it's better to leave it to user
