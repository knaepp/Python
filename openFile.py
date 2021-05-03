import configparser
import os
import smtplib
import requests
import urllib
import hashlib

baseDirectory=""
downloadPath=""
salutation=""
firstSentence=""
fromaddr=""
toaddr=""
msgheader=""
greets=""
greeter=""
SMTPserver=""
AllElements=[]

def getPropertyFile():
    myFile=__file__
    global baseDirectory
    baseDirectory=os.path.dirname(myFile)
    if baseDirectory == "":
        baseDirectory=os.path.abspath(os.path.curdir)
    myFileName=os.path.basename(myFile)
    myFileName=myFileName.split(".")
    return(baseDirectory + os.path.sep + myFileName[0] + ".ini")

def readConfig():
    global downloadPath,salutation,firstSentence,fromaddr,toaddr,msgheader,greets,greeter,SMTPserver,AllElements
    downloadPath=os.path.expanduser(GlobalSection.get("downloadPath"))
    salutation=MailSection.get("salutation")
    firstSentence=MailSection.get("firstSentence")
    fromaddr=MailSection.get("fromaddr")
    toaddr=MailSection.get("toaddr")
    msgheader=MailSection.get("msgheader")
    greets=MailSection.get("greets")
    greeter=MailSection.get("greeter")
    SMTPserver=MailSection.get("SMTPserver")
    AllElements=list(Applications.keys())

def readURLs():
    lines=[]
    #print(AllElements)
    for f in AllElements:
        lines.append(Applications.get(f))
    return lines

def reqJsonFromUrl(dsource):
    r = requests.get( url = dsource )
    data = r.json()
    files = data['aaData']
    return files

def checkTargetPath( tpath ):
    fullpath=tpath
    #print(fullpath)
    if not os.path.exists(tpath):
        os.makedirs(fullpath)

def getFileName(cURL):
    allUrl=cURL.split("/")
    thisFile=allUrl[len(allUrl)-1]
    return thisFile

def fileNotExists(cURL,tarPath):
    thisFile=getFileName(cURL)
    if os.path.exists(tarPath + os.path.sep + thisFile):
        return False
    else:
        return True

def downloadFromURL2(downloadURL, dlPath):
    retVal=True
    try:
        #print("Downloading from " + downloadURL)
        with requests.get(downloadURL, stream=True, timeout=5) as download:
            download.raise_for_status()
            print("Downloading  to " + dlPath)
            print(download.status_code)
            with open(dlPath, 'wb') as fd:
                for chunk in download.iter_content(chunk_size=8192):
                    fd.write(chunk)
    except download.exceptions.Timeout as t:
        retVal=False
        print("HTTP Connection to " + downloadURL + " timed out")
        print(t)
    except download.exceptions.ConnectionErrot as c:
        retVal=False
        print("Error Connecting to " + downloadURL + ": Connection Error")
        print(c)
    except download.exceptions.TooManyRedirects as tmr:
        retVal=False
        print("Too many redirects pointing to " + downloadURL)
        print(tmr)
    finally:
        return retVal


def sendMail(dlFiles):
    body=salutation + "\n" + firstSentence + "\n"
    msg="subject:" + msgheader + "\r\n\r\n" +  body

    for x in dlFiles:
        msg=msg + '\n'
        msg=msg + ''.join(x)
    msg=msg + '\n\n\n' + greets + '\n' + greeter
    server = smtplib.SMTP(SMTPserver)
    server.set_debuglevel(0)
    server.sendmail(fromaddr,toaddr, msg)
    server.quit()

def clearScreen():
    if os.name=="nt":
        os.system("cls")
    else:
        os.system("clear")

def checkURL(myURL):
    startP=myURL.find("https",6)
    myLen=len(myURL)
    myURL=myURL.rstrip("\n\"")
    myURL=myURL[startP:myLen]
    return myURL

def getVendor(urlhost):
    URLComp=urllib.parse.urlparse(urlhost, scheme='', allow_fragments=True)
    hostName=URLComp.hostname.split(".")
    positionHostName=len(hostName) - 2
    HostName=hostName[positionHostName]
    return HostName

def convertPath(myPath):
    if myPath.find('(') > -1:
        myVarB=myPath.encode()
        print(myVarB)
        return hashlib.sha256(myVarB).hexdigest()
    else:
        return myPath

myIniFile=getPropertyFile()
config=configparser.RawConfigParser()
config.read(myIniFile)
GlobalSection=config['Global']
MailSection=config['Mail']
Applications=config['URL']
readConfig()
checkTargetPath(downloadPath)
URLs=readURLs()
downloadedFiles=[]
for c in URLs:
    if len(c)>1:
        myJson=reqJsonFromUrl(str(c))
        Vendor=getVendor(str(c))
        for x in myJson:
            url=x['url']['url']
            if (url.find("https",6) != -1):
                url=checkURL(url)
            model=x['modelName']
            groupName=x['groupName']
            modelTitle=x['title']
            modelTitleDir=convertPath(modelTitle)
            subGroupName=x['subGroupName']
            exactPath=downloadPath + os.path.sep + Vendor + os.path.sep + model + os.path.sep + groupName + os.path.sep + subGroupName
            #print("Processing " + url)
            if not url.startswith("//"):
                if (url.find("apple") == -1):
                    if fileNotExists(url,exactPath):
                        print(exactPath)
                        os.makedirs(exactPath,exist_ok=True)
                        #clearScreen()
                        dlfile=getFileName(url)
                        if downloadFromURL2(url,exactPath + os.path.sep + dlfile):
                                print("Downloading file: ")
                                print(exactPath + os.path.sep + dlfile)
                                downloadedFiles.append(exactPath + os.path.sep + dlfile)
if len(downloadedFiles)>0:
    #os.system('clear')
    sendMail(downloadedFiles)
