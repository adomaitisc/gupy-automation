import os
import json
import requests
import urllib.parse
from dotenv import load_dotenv
from colorama import Fore, Back
from http.cookies import SimpleCookie

load_dotenv()

# The cookies are stored in a .env file, in a string format
# How to collect the cookies in the correct format:
# 1. Login to the gupy website using your browser.
# 2. Open developer tools and open the  console.
# 3. Type without the quotes: "console.log(document.cookie)"
RAW_COOKIES = os.getenv("RAW_COOKIES")

QUERY_URL = "https://portal.api.gupy.io/api/job?name=TITLE&offset=0&limit=LIMIT" # Example: https://portal.api.gupy.io/api/job?name=Internship%20Developer&offset=0&limit=200

APPLY_URL = "URL/candidates/jobs/ID/apply?jobBoardSource=gupy_portal" # Example: https://codenapp.gupy.io/candidates/jobs/1434363446/apply?jobBoardSource=gupy_portal

# Search queries are in Portuguese(BR) because it is the language I am searching in.
# You  can use any language you want as long as gupy is available in it.
SEARCH_QUERIES = [
    "Estagio Front End",
    "Estagio Back End",
    "Estagio Full Stack",
    "Estagio Mobile",
    "Estagio Desenvolvedor",
    "Desenvolvedor Junior"
]
SEARCH_LIMIT = 20 # Limit of jobs to search for each query
REMOTE_ONLY = False # If True, only search for remote jobs

class GupyAutomation:
    def __init__(self, get_jobs=True, apply_jobs=True):
        # get_jobs = True will fetch jobs from the portal
        # get_jobs = False will skip fetching jobs
        # apply_jobs = True will initialize application for jobs
        # apply_jobs = False will skip application

        print(Fore.CYAN + "Initializing..." + Fore.RESET)
        self.cookie_list = self.extract_cookies(RAW_COOKIES)
        self.session = requests.Session()
        self.set_cookies()

        if get_jobs == True:
            print(Fore.YELLOW + "Getting jobs..." + Fore.RESET)
            self.url_list = self.query_to_url(QUERY_URL, SEARCH_QUERIES, SEARCH_LIMIT)
            self.jobs = self.get_jobs_from_url_list(self.url_list)
            self.export_jobs()

        if apply_jobs == True:
            print(Fore.YELLOW + "Applying for jobs..." + Fore.RESET)
            self.jobs = self.read_jobs()
            self.start_applications(self.jobs)
        return

    # Get the cookies from the user input
    # Gets a string and returns a cookie list
    # Example: "cookie1=value1; cookie2=value2" -> {"cookie1": "value1", "cookie2": "value2"}
    def extract_cookies(self, raw_cookies):
        parser = SimpleCookie()
        parser.load(raw_cookies)
        cookies = {k: v.value for k, v in parser.items()}
        return cookies

    # Set cookies to the session
    # Iterates over a cookie list and sets the cookies to the session
    # Example: {"cookie1": "value1", "cookie2": "value2"} -> session.cookies.set("cookie1", "value1")
    def set_cookies(self):
        for k, v in self.cookie_list.items():
            self.session.cookies.set(k, v)
        return

    # Encode the query to be used in the url
    # Takes in a regular string and returns a url encoded string
    # Example: "Internship Front End" -> "Internship%20Front%20End"
    def encode_query(self, query):
        return urllib.parse.quote(query)
    
    # Transform a query list to a url list
    # Takes in a base url and a list of queries and returns a list of urls
    # Example: "https://portal.gupy.io/vagas?searchTerm=" and ["Estagio Front End", ...] -> ["https://portal.gupy.io/vagas?searchTerm=Estagio%20Front%20End", ...]
    def query_to_url(self, base_url, query_list, limit):
        url_list = []
        for i in range(len(query_list)):
            url = base_url.replace("TITLE", self.encode_query(query_list[i])).replace("LIMIT", str(limit))
            url_list.append(url)
        return url_list

    # Query the portal API and get the URLs to the jobs
    # Gets a url and returns a the list of jobs
    def get_jobs_from_url_list(self, url_list):
        job_list = []
        for url in url_list:
            response = self.session.get(url)
            jobs_json = response.json()["data"]
            for job in jobs_json:
                if REMOTE_ONLY == False:
                    job_list.append(self.create_job(job))
                elif REMOTE_ONLY == True and job["isRemoteWork"] == True:
                    job_list.append(self.create_job(job))
        return job_list
    
    # Get application urls from the jobs' data
    # Takes in a list of jobs and returns a list of application urls
    def get_applications(self, job):
        split_url = job["jobUrl"].split("/job")
        apply_url = APPLY_URL.replace("URL", split_url[0]).replace("ID", str(job["id"]))
        return apply_url

    # Return a job object
    # Takes in a json object and returns a created job
    def create_job(self, job):
        return {
            "id": job["id"],
            "title": job["name"],
            "company": job["careerPageName"],
            "isRemote": job["isRemoteWork"],
            "url": job["jobUrl"],
            "applicationUrl": self.get_applications(job)
        }
    
    # Export the jobs data to a json file
    def export_jobs(self):
        with open("output.json", "w") as f:
            json.dump(self.jobs, f)
            f.close()
        return

    # Read the jobs data from a json file
    def read_jobs(self):
        with open("output.json", "r") as f:
            jobs = json.load(f)
            f.close()
        return jobs

    # Start the applications for the jobs
    # Takes in a list of jobs and starts the applications by askinf for user input
    # Example: Apply for job? (y/n/exit) will y: proceed to apply; n: skip; exit: exit the program
    def start_applications(self, jobs):
        for job in jobs:
            print()
            print("Applying for: " + Fore.GREEN + job["title"] + Fore.RESET)
            print("Company: " + Fore.GREEN + job["company"] + Fore.RESET)
            print("Remote: " + Fore.GREEN + str(job["isRemote"]) + Fore.RESET)

            apply = input(Fore.MAGENTA + "Apply for this one? (y/n/exit): ")
            if apply == "exit":
                print()
                print(Fore.RED + "Exiting application.")
                break
            elif apply != "y":
                print(Fore.MAGENTA + "Skipped job." + Fore.RESET)
                print()
            else:
                print(Fore.MAGENTA + "Applying..." + Fore.RESET)

if __name__ == "__main__":
    GupyAutomation(get_jobs=True, apply_jobs=True)

