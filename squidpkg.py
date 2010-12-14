 #! /usr/bin/env python2.6

#squidpkg automatic package deployment. Based on WPKG for Windows.
#Elliot J. Norwood  2010

import os, sys, re, subprocess, shlex
from datetime import datetime
from xml.etree import ElementTree as ET
from socket import gethostname
from optparse import OptionParser

def main():
    #Find local squidpkg directories if they exist, create them if not
    lctemp = os.path.join(localconfig, 'temp')
    lcrepo = os.path.join(localconfig, 'repo')
    if options.debug:
        print (lctemp)
        print (lcrepo)
    if not os.path.isdir(localconfig):
        try:
            os.makedirs(localconfig)
            writeToLog('squidpkg directory created.', 'INFO')
            if options.verbose:
                print ('squidpkg directory created.')
                
        except OSError as e:
            writeToLog(e.args, 'ERROR')
            if options.verbose:
                print (e.args)      
            
    # Initialize log file
    initLog()
    # Check if /etc/squidpkg directory and local config XMl exists
    initLocalConfig()
    
    # Get this hostname's profile
    thisProfile = getHostProf()
    
    # Install the profile
    if thisProfile:
        for profile in thisProfile:
            installProfile(profile)
    else:
        if options.verbose:
            print ('No profile')
        exit(2)
    exit(0) 

def getHostProf():
    #Parse hosts.xml for this host's profile. Check if the host has an indivdual profile or is just part of a group (exactmatch vs. inexactmatch). Return a list of profiles associated with the host. 
    #writeToLog('Finding Hosts...', 'INFO')
    hostTree = parseXML(os.path.join(squidpkg_dir, 'hosts.xml'))
    hostIter = hostTree.getiterator('host')
    exprofList = []
    inprofList = []
    
    for element in hostIter:
        hostnm = element.attrib['name']
        if options.debug:
            print (hostnm)
        
        if hostnm == shorthost:
            exprofList.append(element.attrib['profile-id'])
            subprofiles = element.getiterator('profile')
            for id in subprofiles:
                exprofList.append(id.attrib['id'])
            writeToLog(element.attrib['profile-id'] + ' found.', 'INFO')
            if options.verbose:
                print (str(exprofList) + ' found.')
            exactmatch = exprofList
            break
        else:
            exactmatch = None
            try:
                match = re.search(hostnm, shorthost)
                
            except AttributeError:
                match = None
                pass
            
            if match:
                inprofList.append(element.attrib['profile-id'])
                subprofiles = element.getiterator('profile')
                for id in subprofiles:
                    inprofList.append(id.attrib['id'])
                writeToLog(match.group(0) + ' found.', 'INFO')
                if options.verbose:
                    print (str(inprofList) + ' found.')
                inexactmatch =  inprofList
            else:
                inexactmatch = None
    
    if exactmatch:
        if options.verbose:
            print('exact ')
            print(exactmatch)
        return exactmatch
    elif inexactmatch:
        if options.verbose:
            print('inexact ')
            print (inexactmatch)
        return inexactmatch
    else:
        if not match:
            writeToLog('Hostname ' + shorthost + ' not in Hosts XML. Tried to match to: ' + hostnm, 'ERROR')
            if options.verbose:
                print ('Hostname ' + shorthost + ' not in Hosts XML. Tried to match to: ' + hostnm)
            exit(2)

def initLocalConfig():
    #Check if /etc/squidpkg and localconfig.xml exists. If not create directory and empty XML file.
    if os.path.isfile(localconfigfile):
        writeToLog('Config exists.', 'INFO')
        if options.verbose:
            print ('Config exists')

    else:

        root = ET.Element('packagelist')
        tree = ET.ElementTree(root)
        tree.write(localconfigfile)
        if options.verbose:
            print ('Local config initialized')
        writeToLog('Local config initialized.', 'INFO')

def initLog():
    try:
        f = open(logfile, 'w')
        f.close()
    except IOError as e:
        if options.verbose:
            print (e.args)
            print ('Error initializing log file. Log will not be written.')
        pass

def installPackage(package):
    #Installs the package. Checks localconfig.xml to see if package name and version number match the package to be installed. If not, install the package with install commands in the package XML file. 
    #Updates localconfig file unless there was an error.
    packTree = searchPackages(package)
    packageIter = packTree.getiterator('package')
    checkIter = packTree.getiterator('check')
    installIter = packTree.getiterator('install')
    dependsIter = packTree.getiterator('depends')
    localTree = parseXML(localconfigfile)
    localIter = localTree.getiterator('package')
    localRoot = localTree.getroot()
    updateconfig = True
    
    if not packTree:
        if options.verbose:
            print ('Package not found in ' + package + '.xml')
        writeToLog('Package not found in ' + package + '.xml', 'ERROR')
    else:
        if dependsIter:
            for each in dependsIter:
                if options.debug:
                    print (each.attrib['package-id'])
                installPackage(each.attrib['package-id'])
        
        if not checkIter:
            
            writeToLog('No check condition for ' + package + '. Installing...', 'INFO')
            if options.verbose:
                print ('No check for', package,' Installing...')
            for i in installIter:
                cmd = i.attrib['cmd']
                writeToLog(cmd, 'INFO')
                if options.verbose:
                    print (cmd)
                try:
                    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                    stdout_text, stderr_text = p.communicate()
                    writeToLog(str(stdout_text), 'INFO')
                    if options.verbose:
                        print (stdout_text)
                    if stderr_text:
                        writeToLog(str(stderr_text), 'ERROR')
                        if options.verbose:
                            print (stderr_text)
                        break
                        
                except OSError as e:
                    updateconfig = False
                    error = ''
                    for a in e.args:
                        error = error + ' ' + str(a)
                    writeToLog(error, 'ERROR')
                    break
            
            if not stderr_text:
                writeToLog('Install complete. Local config was not updated.', 'INFO')
                if options.verbose:
                    print('Install Complete')
            else:
                writeToLog('STDERR Occured. Pacakge not installed', 'ERROR')
                if options.verbose:
                    print ('STDERR Occurred')
        
        for item in checkIter:
            checkLine = item.attrib['version']
            if options.debug:
                print (checkLine)
            
            if localIter:
                
                    instName = matchConfigName(package)
                    instVer = matchConfigVer(checkLine)
                        
                    if instName and instVer:
                        writeToLog(package + ' already installed.', 'INFO')
                        if options.verbose:
                            print (package, 'already installed')
                        
                    elif instName:
                        writeToLog('Version mismatch. Upgrading...', 'INFO')
                        if options.verbose:
                            print ('Version mismatch. Upgrading...')
                        for i in installIter:
                            cmd = i.attrib['cmd']
                            writeToLog(cmd, 'INFO')
                            if options.verbose:
                                print (cmd)
                            try:
                                p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                                stdout_text, stderr_text = p.communicate()
                                writeToLog(stdout_text, 'INFO')
                                if options.verbose:
                                    print (stdout_text)
                                if stderr_text:
                                    updateconfig = False
                                    writeToLog(stderr_text, 'ERROR')
                                    if options.verbose:
                                        print (stderr_text)
                                    break
                            except OSError as e:
                                updateconfig = False
                                error = ''
                                for a in e.args:
                                    error = error + ' ' + str(a)
                                writeToLog(error, 'ERROR')
                                break
                            
                        if updateconfig:
                            elem = ET.Element('package')
                            name = packTree.attrib['id']
                            for item in localIter:
                                if item.attrib['name'] == name:
                                    localRoot.remove(item)
                            elem.set('name', name)
                            elem.set('version', checkLine)
                            if options.debug:
                                print (elem)
                            localRoot.append(elem)
                            writeToLog('Upgrade complete.', 'INFO')
                            if options.verbose:
                                print('Upgrade Complete')
                        else:
                            writeToLog('Install Error. Config not updated', 'ERROR')
                            if options.verbose:
                                print('Install Error')
                            
                    else:
                        writeToLog(package + ' not installed. Installing...', 'INFO')
                        if options.verbose:
                            print (package + ' not installed. Installing...')
                        for i in installIter:
                            cmd = i.attrib['cmd']
                            writeToLog(cmd, 'INFO')
                            if options.verbose:
                                print (cmd)
                            try:
                                p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                                stdout_text, stderr_text = p.communicate()
                                writeToLog(str(stdout_text), 'INFO')
                                if stderr_text:
                                    updateconfig = False
                                    writeToLog(str(stderr_text), 'ERROR')
                                    if options.verbose:
                                        print (stderr_text)
                                    break
                            except OSError as e:
                                updateconfig = False
                                error = ''
                                for a in e.args:
                                    error = error + ' ' + str(a)
                                writeToLog(error, 'ERROR')
                                break
                        
                        if updateconfig:
                            elem = ET.Element('package')
                            name = packTree.attrib['id']
                            for item in localIter:
                                if item.attrib['name'] == name:
                                    localRoot.remove(item)
                            elem.set('name', name)
                            elem.set('version', checkLine)
                            if options.debug:
                                print (elem)
                            localRoot.append(elem)
                            writeToLog('Install complete.', 'INFO')
                            if options.verbose:
                                print('Install Complete')
                        else:
                            writeToLog('Install Error. Config not updated', 'ERROR')
                            if options.verbose:
                                print('Install Error')
        
            else:
                writeToLog('Empty configuration. Installing...', 'INFO')
                if options.verbose:
                    print ('Empty configuration. Installing...')
                for i in installIter:
                    cmd = i.attrib['cmd']
                    writeToLog(cmd, 'INFO')
                    if options.verbose:
                        print (cmd)
                    try:
                        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                        stdout_text, stderr_text = p.communicate()
                        writeToLog(str(stdout_text), 'INFO')
                        if stderr_text:
                            updateconfig = False
                            writeToLog(str(stderr_text), 'ERROR')
                            if options.verbose:
                                print (stderr_text)
                            break
                    except OSError as e:
                        updateconfig = False
                        error = ''
                        for a in e.args:
                            error = error + ' ' + str(a)
                        writeToLog(error, 'ERROR')
                        break
                           
                if updateconfig:
                    elem = ET.Element('package')
                    name = packTree.attrib['id']
                    for item in localIter:
                        if item.attrib['name'] == name:
                            localRoot.remove(item)
                    elem.set('name', name)
                    elem.set('version', checkLine)
                    if options.debug:
                        print (elem)
                    localRoot.append(elem)
                else:
                    writeToLog('Install Error. Config not updated.', 'ERROR')
                    if options.verbose:
                        print('Install Error')
    
        localTree.write(localconfigfile)
        writeToLog('Finished installing ' + package, 'INFO')
        if options.verbose:
            print ('Finished installing ' + package)

def installProfile(profile):
    #Parse profiles.xml for list of packages in the given profile. Then call installer function for each package. Also parse for profiles to remove, and call removal function.
    writeToLog('Finding profile...', 'INFO')
    if options.verbose:
        print ('Finding profile...')
    profTree = parseXML(os.path.join(squidpkg_dir, 'profiles.xml'))
    profIter = profTree.getiterator('profile')
    
    for element in profIter:
        profileID = element.attrib['id']
        if options.debug:
            print (profileID)
        
        try:
            match = re.search(profileID, profile)  
        except AttributeError:
            pass

        if match:
            packageIter = element.getiterator('package')
            writeToLog(match.group(0) + ' profile found.', 'INFO')
            if options.verbose:
                print(match.group(0) + ' profile found.')
            break
        
    if not match:
        writeToLog('Profile ' + profile + ' not found in profiles.xml. Create a profile for ' + profile + '.', 'ERROR')
        if options.verbose:
            print ('Profile ' + profile + ' not found in profiles.xml. Create a profile for ' + profile + '.')
        exit(2)

    for subelement in packageIter:
        packageID = None
        removeID = None
        try:
            packageID = subelement.attrib['package-id']
        except KeyError:
            if options.verbose:
                print ('Not a package command')
                #writeToLog('Not a package command', 'INFO')
        if packageID:
            writeToLog('Checking ' + packageID + '...', 'INFO')
            if options.verbose:
                print ('Checking ' + packageID + '...')
            installPackage(packageID)
        else:
            try:
                removeID = subelement.attrib['remove']
            except KeyError:
                if options.verbose:
                    print ('Not a remove command')
                    #writeToLog('Not a remove command', 'INFO')
            if removeID:
                writeToLog('Removing ' + removeID + '...', 'INFO')
                if options.verbose:
                    print ('Removing ' + removeID + '...')
                removePackage(removeID)

    writeToLog('Finished installing profile.', 'INFO')
    if options.verbose:
        print ('Finished installing profile')

def loadPackages():
    #Not in use. Load all the packages into a list.
    packlist = os.listdir(packages_dir)
    trees = []
    packs = []
    fullList = []
    for file in packlist:
        tree = parseXML(os.path.join(packages_dir, file))
        packiter = tree.getiterator('package')
        packs.append(packiter)
    for pack in packs:
        for elm in pack:
            fullList.append(elm.attrib['id'])
            
    packagelist = fullList
    if options.verbose:
        print (fullList)
    #return fulllist

def matchConfigName(package):
    #Check if the package name matches the locally installed name
    localTree = parseXML(localconfigfile)
    localIter = localTree.getiterator('package')
    localRoot = localTree.getroot()
    pkgs = localTree.findall('package')
    
    for p in pkgs:
        if options.debug:
            print (p.attrib['name'])
        if p.attrib['name'] == package:
            return True
        else:
            continue
    return False
    
def matchConfigVer(checkLine):
    #Check if the packge version matches the lcaolly installed version
    localTree = parseXML(localconfigfile)
    localIter = localTree.getiterator('package')
    localRoot = localTree.getroot()
    pkgs = localTree.findall('package')
    
    for p in pkgs:
        if options.debug:
            print (p.attrib['version'])
        try:
            matchver = re.search(p.attrib['version'], checkLine)
            testver = matchver.group(0)
            #print (matchver.group(0) + ' This is the regex') 
        except AttributeError as e:
            #print (e.args, checkLine)
            continue
        
        if matchver:
            return True
        else:
            return False


def parseXML(xml_file):
    #Parse an XML file. Exit if badly formed.
    try:
        xmlf = ET.parse(xml_file)
    except IOError as e:
        if options.verbose:
            print ('Failed parse')
            print (e.args)
        #writeToLog('Error parsing XML in ' + xml_file, 'ERROR')
        exit(2)
        
    return xmlf

def removePackage(package):
    #Removes a package. Will use commands from remove XML tag in package files.
    packTree = searchPackages(package)
    packageIter = packTree.getiterator('package')
    removeIter = packTree.getiterator('remove')
    localTree = parseXML(localconfigfile)
    localIter = localTree.getiterator('package')
    localRoot = localTree.getroot()
    updateconfig = True
    
    if not packTree:
        if options.verbose:
            print ('Package not found in ' + package + '.xml')
        writeToLog('Package not found in ' + package + '.xml', 'ERROR')
    else:
        for i in removeIter:
            cmd = i.attrib['cmd']
            writeToLog(cmd, 'INFO')
            if options.verbose:
                print (cmd)
            try:
                p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                stdout_text, stderr_text = p.communicate()
                writeToLog(stdout_text, 'INFO')
                if stderr_text:
                    writeToLog(stderr_text, 'ERROR')
                    if options.verbose:
                        print (stderr_text)
                    break
                    
            except OSError as e:
                updateconfig = False
                error = ''
                for a in e.args:
                    error = error + ' ' + str(a)
                writeToLog(error, 'ERROR')
                if options.verbose:
                    print (error)
                break
        
        if not stderr_text:
            writeToLog('Uninstall complete.', 'INFO')
            if options.verbose:
                print('Uninstall Complete')
        else:
            writeToLog('STDERR Occured. Package not uninstalled.', 'ERROR')
            if options.verbose:
                print ('STDERR Occurred. Package not uninstalled.')
                    
        if updateconfig:
            elem = ET.Element('package')
            name = packTree.attrib['id']
            for item in localIter:
                if item.attrib['name'] == name:
                    localRoot.remove(item)
        else:
            writeToLog('Uninstall Error. Config not updated.', 'ERROR')
            if options.verbose:
                print('Uninstall Error. Config not updated.')
    
    localTree.write(localconfigfile)
    writeToLog('Finished uninstalling ' + package, 'INFO')
    if options.verbose:
        print ('Finished uninstalling ' + package)

def resetConfig():
    #Reset the local configuration XML file
    os.remove(localconfigfile)
    initLocalConfig()

def searchPackages(package):
    #Search through all package XML files for a specific package. Return if found. Allows for multiple packages per XML file.
    ispkg = False
    packlist = os.listdir(packages_dir)
    for file in packlist:
        tree = parseXML(os.path.join(packages_dir, file))
        packiter = tree.getiterator('package')
        for elm in packiter:
            if elm.attrib['id'] == package:
                ispkg = True
                return elm
                break
            else:
                continue
    if not ispkg:
        writeToLog('Package ' + package + ' not found in packages.', 'INFO')
        print ('Package ' + package + ' not found in packages.')
        return None

def writeToLog(line, status):
    #Write a line to the log. Line is the message string. Status should be INFO, WARNING, or ERROR for easy parsing.
    f = None
    try:
        f = open(logfile, 'a')
    except IOError as e:
        if options.verbose:
            print(e.args)
            print ('Error opening log file. Log will not be written.')
        pass
    t = datetime.now()
    t = t.strftime('%Y-%m-%d %H:%M:%S')
    t = str(t)
    if f:
        f.write(t + ', ' + status + '    : ')
        f.write(line + '\n')
        f.close()

if __name__ == '__main__':
    #Pass command line options to change default paths
    usage = 'Usage: %prog [-prclt]'
    parser = OptionParser(usage)
    parser.add_option('-p', '--path', action='store', type='string', dest='software', help='Set path of software repository.')
    parser.add_option('-r', '--root', action='store', type='string', dest='root', help='Set path of squidpkg root directory.')
    parser.add_option('-c', '--config', action='store', type='string', dest='config', help='Set path of local config XML, else defaults to root directory.')
    parser.add_option('-l', '--log', action='store', type='string', dest='log', help='Set path of log file, else defaults to root directory.')
    parser.add_option('-t', '--hostname', action='store', type='string', dest='host', help='Set hostname variable manually.')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose', help='Show verbose output.')
    parser.add_option('-d', '--debug', action='store_true', dest='debug' help='Show more verbose output. Automatically sets -v in htis mode.')
    (options, args) = parser.parse_args()
    if options.software:
        software = os.path.abspath(options.software)
    else:
        print('Software repository needs to be specified! Run squidpkg.py -h for command line options.')
        exit(2)
    if options.root:
        squidpkg_dir = os.path.abspath(options.root)
        packages_dir = os.path.join(squidpkg_dir, 'packages/')
    else:
        print('squidpkg root needs to be specified! Run squidpkg.py -h for command line options.')
    if options.config:
        localconfig = os.path.abspath(options.config)
        localconfigfile = os.path.join(localconfig, 'localconfig.xml')
    else:
        localconfig = squidpkg_dir
        localconfigfile = os.path.join(localconfig, 'localconfig.xml')
    if options.log:
        host = gethostname()
        hostsplit= host.split('.',1)
        if options.host:
            shorthost = options.host
        else:
            shorthost = hostsplit[0]
        temppath = os.path.join(options.log, ''.join(['squidpkg_', shorthost, '.log']))
        logfile = os.path.abspath(temppath)
    else:
        host = gethostname()
        hostsplit= host.split('.',1)
        if options.host:
            shorthost = options.host
        else:
            shorthost = hostsplit[0]
        temppath = os.path.join(squidpkg_dir, ''.join(['squidpkg_', shorthost, '.log']))
        logfile = os.path.abspath(temppath)
    if options.debug:
        options.verbose = True
        
        
    # Someone is launching this directly
    main()
        