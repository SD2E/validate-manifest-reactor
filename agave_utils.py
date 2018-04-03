import re
import os
import logging
import time

FILES_HTTP_LINK_TYPES = ('media', 'download')
FILES_COMPATIBLE_APIS = ('files', 'jobs')
PWD = os.getcwd()

# TODO: Support nonces
# TODO: Support sending URL parameters
# TODO: Support binary FIFO?
def message_reactor(agaveClient, actorId, message, ignoreErrors=True):
    """
    Send a message to an Abaco actor
    * Returns execution ID
    * If ignoreErrors is True, this is fire-and-forget. Otherwise, failures
      will raise an Exception that must be handled by the caller
    """
    print("Reactor {}".format(actorId))
    print(" Message: {}".format(message))

    execution = {}
    try:
        execution = agaveClient.actors.sendMessage(actorId=actorId,
                                                   body={'message': message})
    except Exception as e:
        errorMessage = "Error messaging actor {}: {}".format(actorId, e)
        if ignoreErrors:
            logging.warning(errorMessage)
            pass
        else:
            raise Exception(errorMessage)

    try:
        execId = execution.executionId
        print(" Exec: {}".format(execId))
        return execId
    except Exception as e:
        errorMessage = " Message to {} failed: {}".format(actorId, e)
        if ignoreErrors:
            logging.warning(errorMessage)
            pass
        else:
            raise Exception(errorMessage)


def agave_mkdir(agaveClient, dirName, systemId, basePath='/'):
    """
    Creates a directory on an Agave storage system with the specified
    base path. Like mkdir -p this is imdepotent and will create the
    entire path tree required so long as paths are specified correctly
    """
    try:
        agaveClient.files.manage(systemId=systemId,
                                 body={'action': 'mkdir', 'path': dirName},
                                 filePath=basePath)
    except Exception as e:
        raise Exception(
            "Unable to mkdir {} at {}/{}: {}".format(
                dirName, systemId, basePath, e))

    return True


def agave_download_file(agaveClient,
                        agaveAbsolutePath,
                        systemId,
                        localFilename='downloaded',
                        sync=True):
    """
    Download an Agave-hosted remote file to local storage in cwd
    * Always synchronous (for now)
    """
    downloadFileName = os.path.join(PWD, localFilename)
    with open(downloadFileName, 'wb') as f:
        rsp = agaveClient.files.download(systemId=systemId,
                                         filePath=agaveAbsolutePath)
        if type(rsp) == dict:
            logging.critical(
                "Error downloading file. Got dict response: {}".format(rsp))
            raise Exception(
                "Unable to download {}".format(agaveAbsolutePath))
        for block in rsp.iter_content(2048):
            if not block:
                break
            f.write(block)
    return downloadFileName


def agave_upload_file(agaveClient,
                      agaveDestPath,
                      systemId,
                      uploadFile,
                      sync=True,
                      timeOut=90):
    """
    Upload a file to remote storage.
    * If sync==True, wait for the upload to complete on the backend before
      returning. Raises exceptions on importData or timeout errors.
      """
    try:
        agaveClient.files.importData(systemId=systemId,
                                     filePath=agaveDestPath,
                                     fileToUpload=open(uploadFile))
    except Exception as e:
        raise Exception("Error uploading {}: {}".format(uploadFile, e))

    uploaded_filename = os.path.basename(uploadFile)
    if sync:
        fullAgaveDestPath = os.path.join(agaveDestPath, uploaded_filename)
        wait_for_file_status(
            agaveClient, fullAgaveDestPath, systemId, timeOut)

    return True


def wait_for_file_status(agaveClient, agaveWatchPath,
                         systemId, maxTime=300):
    """
    Synchronously wait for a files path to reach a terminal state
    Returns an exception and the final state if it takes longer
    then maxTime seconds. Returns True on success.
    """
    TERMINAL_STATES = ['CREATED', 'TRANSFORMING_COMPLETED']

    assert maxTime > 0
    assert maxTime <= 1000

    delay = 0.150  # 300 msec
    expires = (time.time() + maxTime)
    stat = None
    ts = time.time()

    while (time.time() < expires):
        elapsed = time.time() - ts
        try:
            hist = agaveClient.files.getHistory(systemId=systemId,
                                                filePath=agaveWatchPath)
            stat = hist[-1]['status']
            if stat in TERMINAL_STATES:
                logging.info("Elapsed time: {} sec".format(elapsed))
                return True
        except Exception as e:
            # we have to swallow this exception because status isn't available
            # until the files service picks up the task. sometimes that's
            # immediate and sometimes it's backlogged - we dont' want to fail
            # just because it takes a few seconds or more before status becomes
            # available since we went through the trouble of setting up
            # exponential backoff!
            logging.warning(
                "Couldn't get status of agave://{}/{} ({})".format(
                    systemId, agaveWatchPath, e))
            pass
        time.sleep(delay)
        delay = (delay * 1.1)

    raise Exception(
        "Status transition for {} exceeded {} sec. Last status: {}".format(
            agaveWatchPath, maxTime, stat))


def to_agave_uri(systemId=None, dirPath=None, fileName=None, validate=False):
    """
    Returns an Agave URI for a given system ID, path, (filename)
    * Validation that URI points to a real resource is not implemented.
      Should we choose to do this, it will be expensive since it will
      involve at least one API call
    """
    if (systemId is not None) and (dirPath is not None):
        uri = 'agave://' + systemId + os.path.join('/', dirPath)
        if fileName is not None:
            uri = os.path.join(uri, fileName)
        return uri
    else:
        raise ValueError('Both systemId and dirPath must be specified')


def from_tacc_s3_uri(uri=None, Validate=False):
    """
    Returns a tuple of systemId, directoryPath, (fileName) from Agave URI
    * Validation that it points to a real resource is not implemented. The
      same caveats about validation apply here as in to_agave_uri()
    """
    systemId = None
    dirPath = None
    fileName = None

    proto = re.compile("s3:\/\/(.*)$")

    if uri is None:
        raise Exception("URI cannot be empty")
    resourcepath = proto.search(uri)
    if resourcepath is None:
        raise Exception("Unable resolve URI")
    resourcepath = resourcepath.group(1)

    firstSlash = resourcepath.find('/')
    if firstSlash is -1:
        raise Exception("Unable to resolve systemId")

    try:
        systemId = 'data-' + resourcepath[0:firstSlash]
        origDirPath = resourcepath[firstSlash + 1:]
        dirPath = '/' + os.path.dirname(origDirPath)
        fileName = os.path.basename(origDirPath)
        if fileName is '':
            fileName = '/'
    except Exception as e:
        raise Exception(
            "Error resolving directory path or file name: {}".format(e))

    return(systemId, dirPath, fileName)

def from_agave_uri(uri=None, Validate=False):
    """
    Returns a tuple of systemId, directoryPath, (fileName) from Agave URI
    * Validation that it points to a real resource is not implemented. The
      same caveats about validation apply here as in to_agave_uri()
    """
    systemId = None
    dirPath = None
    fileName = None

    proto = re.compile("agave:\/\/(.*)$")

    if uri is None:
        raise Exception("URI cannot be empty")
    resourcepath = proto.search(uri)
    if resourcepath is None:
        raise Exception("Unable resolve URI")
    resourcepath = resourcepath.group(1)

    firstSlash = resourcepath.find('/')
    if firstSlash is -1:
        raise Exception("Unable to resolve systemId")

    try:
        systemId = resourcepath[0:firstSlash]
        origDirPath = resourcepath[firstSlash + 1:]
        dirPath = '/' + os.path.dirname(origDirPath)
        fileName = os.path.basename(origDirPath)
        if fileName is '':
            fileName = '/'
    except Exception as e:
        raise Exception(
            "Error resolving directory path or file name: {}".format(e))

    return(systemId, dirPath, fileName)


"""
https://api.sd2e.org/files/v2/media/system/data-sd2e-projects-users//vaughn/jupyter-agave-test/exp2801-04-ds731218.msf
https://api.sd2e.org/files/v2/download/vaughn/system/data-sd2e-community/sample/jupyter/notebooks/meslami-SD2_Quicklooks_Combined_v4.ipynb
"""
def agave_uri_from_http(httpURI=None):
    """
    Convert an HTTP(s) URI to its agave:// format
    * Do not use yet
    """
    agaveURI = None
    proto = re.compile("http(s)?:\/\/(.*)$")
    resourcePath = proto.search(httpURI)
    if resourcePath is None:
        raise ValueError('Unable resolve ' + httpURI)
    resourcePath = resourcePath.group(2)
    elements = resourcePath.split('/')
    elements = list(filter(None, elements))
    apiServer, apiEndpoint, systemId = (elements[0], elements[1], None)
    if '/download/' in resourcePath:
        systemId = elements[6]
        sysPath = '/'.join(elements[7:])
    elif '/media/' in resourcePath:
        systemId = elements[5]
        sysPath = '/'.join(elements[6:])

    agaveURI = 'agave://{}/{}'.format(systemId, sysPath)
    return agaveURI


# TODO - Formalize how to acquire tenant api server and username. Will
#        require having an active Agave client
def http_uri_from_agave(agaveURI=None, linkType='media', userName='public'):
    """
    Returns an http(s) media URL for data movement or download
    * Do not use yet.
    """
    httpURI = None

    typeSlug = '/'

    if linkType not in FILES_HTTP_LINK_TYPES:
        raise ValueError('linkType ' + linkType + ' not a valid value')
    elif linkType == 'media':
        typeSlug = 'media/'
    else:
        typeSlug = 'download/' + userName + '/'

    systemId, dirPath, fileName = from_agave_uri(agaveURI)
    httpURI = 'https://api.tacc.cloud/files/v2/' + typeSlug + \
        'system/' + systemId + '/' + dirPath + fileName
    return httpURI
