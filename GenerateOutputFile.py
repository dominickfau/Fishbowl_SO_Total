import csv
import os
import os.path
import sys
import getopt
import logging
from logging.handlers import RotatingFileHandler

class GenerateData(object):
    OUTPUT_FILE_NAME = "Compiled Output.csv"
    OUTPUT_FILE_HEADERS = ["Date", "Parts Over Due", "$ Over Due", "Total Parts", "Total $"]

    LOG_FILE_NAME = "Log.txt"
    LOG_FILE_MAX_SIZE = 100 # Size in kb

    def __init__(self):
        self.fileNames = []
        self.outputList = []
        self.sortedOutputList = []
        self.createLogger()

    def createLogger(self, logVerbosity="INFO"):
        log_formatter = logging.Formatter('%(asctime)s  %(name)s - %(levelname)s: %(message)s')

        my_handler = RotatingFileHandler(self.LOG_FILE_NAME, mode='a', maxBytes=self.LOG_FILE_MAX_SIZE * 1000, 
                                        backupCount=2, encoding=None, delay=0)
        my_handler.setFormatter(log_formatter)
        my_handler.setLevel(logging.INFO)

        self.logger = logging.getLogger('Root')

        self.logger.addHandler(my_handler)

        startMessage = "[START] Program started."

        # Add start message on startup.
        self.logger.setLevel("INFO")
        self.logger.info(startMessage)

        # Setting the threshold of logger
        self.logger.setLevel(logVerbosity)
        return


    def getRawDataFileNames(self, pathToWalk):
        self.logger.info(f"Retreiving all file names from path: '{pathToWalk}'")
        _, _, self.fileNames = next(os.walk(pathToWalk))
        self.logger.info(f"Filenames found: {self.fileNames}")
        return self.fileNames


    def sortList(self):
        self.logger.info("Sorting output list.")
        self.sortedOutputList = sorted(self.outputList, key=lambda x: x['date'])
        self.logger.info("Done.")
        return self.sortedOutputList


    def getFilesToProcess(self, pathToRawData):
        self.logger.info(f"Reading CSV files from path: {pathToRawData}")
        self.outputList = []
        for fileName in self.fileNames:
            self.logger.info(f"Reading file: '{fileName}'")
            with open(os.path.abspath(os.path.join(pathToRawData, fileName)), mode='r', newline='\n') as csvFile:
                for line in csv.DictReader(csvFile):
                    self.outputList.append(line)
        return self.outputList


    def writeOutputFile(self, saveToPath, fileName, headers):
        self.logger.info(f"Writing output filename: '{fileName}'' to path: '{saveToPath}'")
        with open(os.path.abspath(os.path.join(saveToPath, fileName)), mode='w', newline='\n') as csvFile:
            csvWriter = csv.writer(csvFile)
            csvWriter.writerow(headers)
            for item in self.sortedOutputList:
                toWrite = [item['date'], float(item['totalQtyOverDue']), float(item['totalPriceOverDue']), float(item['totalQty']), float(item['totalPrice'])]
                csvWriter.writerow(toWrite)
        self.logger.info("Done.")


    def removeFishbowlFiles(self, pathToRawData):
        self.logger.info(f"Removing all Fishbowl generated files from path: {pathToRawData}")
        allFiles = self.getRawDataFileNames(pathToRawData)

        for filename in allFiles:
            if filename != "PreviousData.csv":
                self.logger.info(f"Removing filename: '{filename}'")
                file_path = os.path.join(pathToRawData, filename)
                os.unlink(file_path)
        return


    def backupCurrentOutputFile(self, pathToSaveOutputFile, outputFileName):
        if os.path.isfile(os.path.join(pathToSaveOutputFile, outputFileName)):
            backupFileName = outputFileName.split('.csv')[0]
            backupFileName = "Backup_" + backupFileName + ".csv"
            with open(os.path.join(pathToSaveOutputFile, outputFileName), mode='r', newline='\n') as csvFile:
                lines = csvFile.readlines()

            with open(os.path.join(pathToSaveOutputFile, backupFileName), mode='w', newline='\n') as csvFile:
                csvFile.writelines(lines)


    def run(self, pathToRawData, pathToSaveOutputFile, outputFileName, outputFileHeaders, openFile=False, forceRun=False):
        self.logger.info("Starting...")
        try:
            self.getRawDataFileNames(pathToRawData)
        except StopIteration:
            self.logger.error(f"Path to raw data does not exist. Path: '{pathToRawData}'")
            return

        if forceRun:
            self.logger.warning("Option forceRun set True. Output file generation will bypass raw folder checks.")
            self.backupCurrentOutputFile(pathToSaveOutputFile, outputFileName)

        if openFile: self.logger.info("Option openFile set True. Output file will try to open when finished.")

        if len(self.fileNames) <= 1 and not forceRun:
            try:
                fileName = self.fileNames[0]
                if fileName == "PreviousData.csv":
                    self.logger.warning("No Fishbowl files to process. Stoping file processing.")
                    return
            except IndexError:
                pass
        self.getFilesToProcess(pathToRawData)
        self.sortList()

        # Save main output file
        self.writeOutputFile(pathToSaveOutputFile, outputFileName, outputFileHeaders)

        # Save output file to hold all current data, then remove Fishbowl generated files.
        self.writeOutputFile(pathToRawData, "PreviousData.csv", ["date", "totalQtyOverDue", "totalPriceOverDue", "totalQty", "totalPrice"])
        self.removeFishbowlFiles(pathToRawData)
        self.logger.info(f"Finished processing files. Compiled output file can be found at: {os.path.join(pathToSaveOutputFile, outputFileName)}")
        self.logger.info("-" * 40)
        
        if openFile:
            os.startfile(os.path.abspath(os.path.join(pathToRawData, outputFileName)))

if __name__ == "__main__":
    rawDataPath = ""
    saveOutputPath = ""
    openFile = False
    forceRun = False

    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "x:o:af")
    except Exception:
        print(f"[ERROR] Options -x and -o are both required, optionally -a can be used to automatically open the output file when processing finishes and -f forces output file to compile.\n\tDo not include the slash at the end of either strings. -x = full path to raw CSV files. -o = full file path to save output CSV file to.")
        exit()

    for opt, arg in opts:
        if opt in ['-x']:
            rawDataPath = arg
        elif opt in ['-o']:
            saveOutputPath = arg
        elif opt in ['-a']:
            openFile = True
        elif opt in ['-f']:
            forceRun = True

    # Check if folder paths are valid.
    if not os.path.isdir(rawDataPath):
        print(f"[ERROR] Raw folder path: '{rawDataPath}' is not a valid path. Did the string include the slash at the end? If so remove and try again.")
        exit()
    if not os.path.isdir(saveOutputPath):
        print(f"[ERROR] Output folder path: '{saveOutputPath}' is not a valid path. Did the string include the slash at the end? If so remove and try again.")
        exit()

    f = GenerateData()
    f.run(  pathToRawData = rawDataPath,
            pathToSaveOutputFile = saveOutputPath,
            outputFileName = f.OUTPUT_FILE_NAME,
            outputFileHeaders = f.OUTPUT_FILE_HEADERS,
            openFile = openFile,
            forceRun = forceRun)
    print("Finished.")