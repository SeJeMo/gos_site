import psycopg2
from configparser import ConfigParser

def readConf(conf='config.ini', sections='postgresql'):
    parseObj = ConfigParser()
    parseObj.read(conf)
    databaseOpts = {}
    if parseObj.has_section(sections):
        confData = parseObj.items(sections)
        for d in confData:
            databaseOpts[d[0]] = d[1]
        return databaseOpts

def get_db_connection():
    params = readConf()
    conn = psycopg2.connect(**params)
    return conn