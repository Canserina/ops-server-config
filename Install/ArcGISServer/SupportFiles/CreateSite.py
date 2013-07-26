#==============================================================================
#Name:          CreateSite.py
#Purpose:       Creates the ArcGIS Server site.
#
#Prerequisites: ArcGIS Server must be installed and authorized before
#               executing this script.
#
#History:       2012:   Initial code.
#
#==============================================================================
import os, sys, traceback

# Add ConfigureOpsServer\SupportFiles to sys path inorder to import
#   modules in subfolder
supportFilesPath = os.path.join(
    os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0])))), "SupportFiles")

sys.path.append(supportFilesPath)

import OpsServerConfig
from Utilities import makePath
from UtilitiesArcPy import createAGSConnectionFile
from UtilitiesArcPy import checkResults

# For Http calls
import httplib, urllib, json

servername = OpsServerConfig.serverName
serverDrive = OpsServerConfig.serverDrive
serverPort = OpsServerConfig.serverPort


# Defines the entry point into the script
def createSite(username, password, dataDrive, cacheDrive):

    success = True
    
    try:
        print
        print "--Create ArcGIS Server Site..."
        print
        
        agsCache = OpsServerConfig.getCacheRootPath(cacheDrive)
        
        pathList = ["arcgisserver"]
        agsData = makePath(dataDrive, pathList)
        
        pathList = ["OpsServer", "arcgisserver", "config-store"]
        agsConfig = makePath(serverDrive, pathList)
    
        # Set up required properties for config store
        print "\t-Setting up required properties for config store..."
        configStoreConnection={"connectionString": agsConfig, "type": "FILESYSTEM"}
        print "\tDone."
        print
     
        # Set up paths for server directories             
        jobsDirPath = os.path.join(agsData, "arcgisjobs")
        outputDirPath = os.path.join(agsData, "arcgisoutput")
        systemDirPath = os.path.join(agsData, "arcgissystem")
       
        # Create Python dictionaries representing server directories
        print "\t-Creating Python dictionaries representing server directories"
        print "\t\t(arcgiscache, arcgisjobs, arcgisoutput, arcgissystem)..."
        cacheDir = dict(name = "arcgiscache",physicalPath = agsCache,directoryType = "CACHE",cleanupMode = "NONE",maxFileAge = 0,description = "Stores tile caches used by map, globe, and image services for rapid performance.", virtualPath = "")    
        jobsDir = dict(name = "arcgisjobs",physicalPath = jobsDirPath, directoryType = "JOBS",cleanupMode = "TIME_ELAPSED_SINCE_LAST_MODIFIED",maxFileAge = 360,description = "Stores results and other information from geoprocessing services.", virtualPath = "")
        outputDir = dict(name = "arcgisoutput",physicalPath = outputDirPath,directoryType = "OUTPUT",cleanupMode = "TIME_ELAPSED_SINCE_LAST_MODIFIED",maxFileAge = 10,description = "Stores various information generated by services, such as map images.", virtualPath = "")
        systemDir = dict(name = "arcgissystem",physicalPath = systemDirPath,directoryType = "SYSTEM",cleanupMode = "NONE",maxFileAge = 0,description = "Stores files that are used internally by the GIS server.", virtualPath = "")
        print "\tDone."
        print
    
        # Serialize directory information to JSON
        print "\t-Serializing server directory information to JSON..."
        directoriesJSON = json.dumps(dict(directories = [cacheDir, jobsDir, outputDir, systemDir]))      
        print "\tDone."
        print
        
        # Construct URL to create a new site
        print "\t-Constructing URL to create a new site..."
        createNewSiteURL = "/arcgis/admin/createNewSite"
        print "\tDone."
        print
        
        # Set up parameters for the request
        print "\t-Setting up parameters for the request to create new site..."
        params = urllib.urlencode({'username': username, 'password': password, 'configStoreConnection': configStoreConnection, 'directories':directoriesJSON, 'f': 'json'})
        
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        print "\tDone."
        print
        
        # Connect to URL and post parameters
        print "\t-Making request to create new site..."
        httpConn = httplib.HTTPConnection(servername, serverPort)
        httpConn.request("POST", createNewSiteURL, params, headers)
        
        # Read response
        response = httpConn.getresponse()
        if (response.status != 200):
            httpConn.close()
            print "\tERROR: Error while creating the site."
            print
            success = False
        else:
            data = response.read()
            httpConn.close()
            
            # Check that data returned is not an error object
            if not assertJsonSuccess(data):          
                print "\tERROR: Error returned by operation. " + str(data)
                print
            else:
                print "\tSite created successfully."
                print "\tDone."
                print
         
    except:
        success = False
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
     
        # Concatenate information together concerning the error into a message string
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        
        # Print Python error messages for use in Python / Python Window
        print
        print "***** ERROR ENCOUNTERED *****"
        print pymsg + "\n"
        
    finally:
        # Return success flag
        return success    

# A function that checks that the input JSON object 
#  is not an error object.
def assertJsonSuccess(data):
    obj = json.loads(data)
    if 'status' in obj and obj['status'] == "error":
        print "Error: JSON object returns an error. " + str(obj)
        return False
    else:
        return True


def createAGSConnFile(username, password):

    success = True
    printMsg = True

    try:
        print
        print "--Create ArcGIS Administrative connection file..."
        print
        
        # Set connection folder and file variables
        fileRoot = "ConfigureOpsServer"
        scriptPath = sys.argv[0]
        agsConnFolderPath = scriptPath[:(scriptPath.find(fileRoot) + len(fileRoot))]
        agsConnFile = "OpsServer_admin.ags"
        agsConnFilePath = agsConnFolderPath + os.sep + agsConnFile
        
        # Create ArcGIS Server connection file
        print "\tCreating admin connection file " + agsConnFilePath + "..."
        
        results = createAGSConnectionFile(agsConnFolderPath, agsConnFile, servername,
                            username, password, serverPort)
        success = checkResults(results, printMsg)
            
    except:
        success = False
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
     
        # Concatenate information together concerning the error into a message string
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        
        # Print Python error messages for use in Python / Python Window
        print
        print "***** ERROR ENCOUNTERED *****"
        print pymsg + "\n"
        
    finally:
        # Return success flag
        return success    
        
# Script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))