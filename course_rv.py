#!/usr/bin/python3


""" Automated interface for the CU Boulder Class Scheduling Site
"""

import requests
from docopt import docopt
from getpass import getpass
import json
from lxml import html

doc_str = """Class Rendez-Vous

Usage:
  class_rv.py search dept <dpt> course_num <cn> [--section=<sctn> | --gt]  
  class_rv.py add class <dept> <course_num> <section>  
  class_rv.py checkout all 
  class_rv.py
  class_rv.py -h | --help
  class_rv.py --version

Options:
  -h --help         Show this screen.
  --version         Show version.
  --gt              Greater than in Course nuber search
  --section=<sctn>  Specify the sectionnumber if known
  -c --conflict     Ignore conflicting Time slots with already enrolled classes
  -o --open         Only show open courses.
"""



def class_search_form():
    fields = {
        'SSR_CLSRCH_WRK_CAMPUS$0':'BLDR',            # Campus    {'BLDR':'Boulder Campus'}
        'SSR_CLSRCH_WRK_SUBJECT$1':'ECEN',           # Department 
        'SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$2':'G',     # Exact Match? {'G':'Greater Than', 'T':'Less Than', 'E':'Equal To'}
        'SSR_CLSRCH_WRK_CATALOG_NBR$2':5000,         # Catalog Nnumber
        'SSR_CLSRCH_WRK_ACAD_CAREER$3':'',           # Academic Career {'Grad':'Graduate',}
        'SSR_CLSRCH_WRK_SSR_OPEN_ONLY$chk$4':'N',    # Only open sections?
        'SSR_CLSRCH_WRK_CU_SCHD_CNFLCT_FLG$chk$5':'' # Ignore schedule Conflicts
    }
    cookies = {
        'sto-id-47873-finprd_8443':'ICAJBCKMPLCA',
        'sto-id-47873-icsprd_8510':'CLAJBCKMDOCB',
        'sto-id-47873-pcrmweb_8530':'BIAJBCKMFCCB',
        'sto-id-hr-47873':'IAAJBCKMPLCA'
    }
def main(args):
    #login_form['j_username'] = input("Username:")
    #login_form['j_password'] = getpass()
    inputRaw = open('details.json','r')
    login_form = json.load(inputRaw)

    headers0={
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/59.0.3071.109 Chrome/59.0.3071.109 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.8'
    }

    headers={
        'connection':'keep-alive',
        'referer':'https://portal.prod.cu.edu/MyCUInfoFedAuthLogin.html',
        'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/59.0.3071.109 Chrome/59.0.3071.109 Safari/537.36',
        'origin':'https://fedauth.colorado.edu'
    }

    url0 = 'https://ping.prod.cu.edu/idp/startSSO.ping?PartnerSpId=SP:EnterprisePortal&IdpSelectorId=BoulderIDP&TargetResource=https://portal.prod.cu.edu%2Fpsp%2Fepprod%2FUCB2%2FENTP%2Fh%2F%3Ftab%3DDEFAULT'
    url1 = 'https://fedauth.colorado.edu/idp/profile/SAML2/POST/SSO' 
    url2 = 'https://fedauth.colorado.edu/idp/profile/SAML2/POST/SSO;jsessionid={}?execution=e1s1'
    url3 = 'https://ping.prod.cu.edu/sp/ACS.saml2'

    with requests.Session() as s: 
        #============================[ step 1 ]===============================
        #  Initiate the SSO With the Service Providder [SP] 

        # Get PF cookie expecting code 200
        print('[ 1.0 ]','GET', url0)
        res = s.get(url0, headers=headers, allow_redirects=True)
        print(res.cookies)

        tree = html.fromstring(res.content)
        SAMLRequest = tree.xpath('//input[@name="SAMLRequest"]')[0].value
        RelayState = tree.xpath('//input[@name="RelayState"]')[0].value
        #print(SAMLRequest, RelayState)

        PF = s.cookies.get('PF')
        s.cookies.clear_session_cookies() 
        print(res.status_code, s.cookies, '\n\n')
        
        # Get JSESSIONID Cookie 
        # expect 302 redirect to https://fedauth.colorado.edu/idp/profile/SAML2/POST/SSO;jsessionid=CD3972227220E0DDD2EBCDDA0BBDB608?execution=e1s1
        print('[ 1.0 ]', 'POST', url1)
        headers['referer'] = 'https://ping.prod.cu.edu/'
        headers['origin'] = 'https://ping.prod.cu.edu/'
        headers['content-type'] = 'application/x-www-form-urlencoded'
        form_data = {'SAMLResponse':SAMLRequest, 'RelayState':RelayState}
        res = s.post(url1,data=form_data, allow_redirects=True)
        print(res.status_code, s.cookies)
        print(res.headers, '\n\n')
        
        JSID = s.cookies.get('JSESSIONID')
        url2 = url2.format(JSID)

        #============================[ step 2 ]===============================
        # Authenticate with the Identity Provider  [IdP]

        # Get the shib_idp_session cookie - expect status 200
        headers['referer'] = url2
        print('[ 2.0 ]', 'POST', url2)
        res = s.post(url2, headers=headers, data=login_form, allow_redirects=True)
        print(res.status_code, s.cookies)
        #print(res.content)
        shib_idp_session = s.cookies.get('shib_idp_session')
    
        tree = html.fromstring(res.content)
        SAMLResponse = tree.xpath('//input[@name="SAMLResponse"]')[0].value
        RelayState = tree.xpath('//input[@name="RelayState"]')[0].value
        #RelayState = 'https://portal.prod.cu.edu/psp/epprod/UCB2/ENTP/h/?tab=DEFAULT'
        #print(SAMLResponse, RelayState)
        print(res.headers, '\n\n') 


        # SAML Request ONE 
        s.cookies.clear_session_cookies() 
        s.cookies.set('PF',PF)
        headers['referer'] = url2
        headers['pragma'] = 'no-cache'
        headers['origin'] = 'https://fedauth.colorado.edu'
        headers['host'] = 'ping.prod.cu.edu'
        headers['content-type'] = 'application/x-www-form-urlencoded'
        # headers['referer-policy'] = 'no-referrer-when-downgrade'
        saml1_data = {'SAMLResponse':SAMLResponse, 'RelayState':RelayState}
        print(s.cookies)
        print(headers)
        print('[ 3.0 ]', 'POST', url3)
        res = s.post(url3, headers=headers, allow_redirects=True, data=saml1_data)
        print(res.status_code, s.cookies)
        tree = html.fromstring(res.content)
        SAMLResponse = tree.xpath('//input[@name="SAMLResponse"]')[0].value
        RelayState = tree.xpath('//input[@name="RelayState"]')[0].value
        print(res.headers, '\n\n')


        #============================[ step 3 ]===============================
        # Get opentoken from CU Bouler SAML Shibboleth server 

        # SAML Request TWO - Get opentoken
        headers['referer'] = 'https://ping.prod.cu.edu'
        headers['origin'] = 'https://ping.prod.cu.edu/'
        headers['referer-policy'] = 'origin'
        saml2_data = {'SAMLResponse':SAMLResponse, 'RelayState':RelayState}
        print('[ 3.1 ]', 'POST', url3)
        res = s.post(url3, headers=headers, allow_redirects=True, data=saml2_data)
        print(res.status_code, s.cookies)
        print(res.content)
        print(res.headers, '\n\n')


if __name__ == '__main__':
    args = docopt(doc_str, version='Class Rendez-Vous 1.0')
    #print(args),
    main(args)
