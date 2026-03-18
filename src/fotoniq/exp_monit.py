#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ----------------------------------
# Created on the Mon Feb 23 2026 by Victor
#
# Copyright (c) 2026 - AmazingQuantum@UChile
# ----------------------------------
#
"""
Content of exp_monit.py

Please document your code ;-).

"""


from fotoniq.logger import getLogger
from influxdb import InfluxDBClient
from zoneinfo import ZoneInfo
import numpy as np 
import pandas as pd
from datetime import datetime, timezone, timedelta
log = getLogger(__name__)

DEFAULT_TZ =ZoneInfo("America/Santiago")

class ExpMonClient(InfluxDBClient):
    def __init__(self, 
                 database = "amazQdatabase",
                 host = "127.0.0.1",
                 port = 8086,
                 use_buffer=True,
                 buffer_size = 50,
                 **kwargs
                 ):
        """
        InfluxDB Client for experiment monitoring.

        Args:
            database (str): Name of the database to connect to.
            host (str): IP address of the InfluxDB server (use 127.0.0.1 for SSH tunnels).
            port (int): Port number (default: 8086).
            use_buffer (bool, optional): if true, we do not write on the database each time the method write is called. Instead, we write the data in. buffer of size buffer_size and write all points at once. This allowed to weight down the job of the SBC4.
            buffer_size (int, optional): the size of the buffer, sets the number of points we wait until to write onto the database.
            **kwargs: Additional arguments passed to InfluxDBClient (timeout, SSL, etc.).

        Essential inherited methods:
        --- METADATA & INFO ---
        - get_list_database()        : List all existing databases.
        - get_list_measurements()    : List tables (measurements) in current DB.
        - get_list_series(msmnt)     : List unique tag combinations for a measurement.
        - switch_database(name)      : Change active database context.

        --- DATA EXTRACTION ---
        - query(str)                 : Execute InfluxQL (e.g., 'SELECT * FROM "m"').
        - result.get_points()        : Access data points from a query result.
        
        """
        self.use_buffer = use_buffer
        self.buffer_size = buffer_size
        self.buffer = []
        super().__init__(
            database=database,
            host=host,
            port=port
        )
        self.check_connection()


    def check_connection(self):
        """check connection to the database and raise an Error if the connection does not exists."""
        try:
            _= self.get_list_database()
        except Exception as e:
            msg="\n\n"+"="*10+" HELP "+"="*10+"\n"+f"""
Connection to the client database failed. Make sure you really manually maped the remote InfluxDB port (127.0.0.1:8086, a priori) to  your local machine ({self._host}:{self._port}). If not, you can do it running in a separate Terminal:\n
ssh -L {self._port}:127.0.0.1:8086 root@172.17.55.144\n
and make sure host = '127.0.0.1' and port = 8086 when instanciating the class. Once the terminal is connected, check again.

If you are running the code on the experiment Windows computer, simply lunch the Tunnel_influx bat file (on the Desktop).
"""         
            log.error(f"InfluxDB connection failed on {self._host}:{self._port}.")
            raise ConnectionError(str(e)+msg) from None
        
    def delete_measurement(self, 
                           measurement, 
                           tstart=datetime(2026, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
                           tstop=datetime.now(timezone.utc),
                           ):
        """Delete a measurement from the database between two dates.

        Parameters
        ----------
        measurement : str
            the name of the measurement to delete
        tstart : datetime object, optional
            the first time at which the measurement is supressed, by default datetime(2026, 1, 1, 0, 0).tzinfo=ZoneInfo("UTC") i.e. lab inauguration.
        tstop : datetime object, optional
            the last time for the measruement is suppressed, by default now i.e.  datetime.now(timezone.utc)
        """
        if measurement not in self.get_measurements_list():
            log.warning(f"Measurement {measurement} is not in the database.")
            return 
        tstart_str, tstop_str = self.format_time_for_InfluxDB(tstart), self.format_time_for_InfluxDB(tstop)
        query = f"DELETE FROM \"{measurement}\" WHERE time >= '{tstart_str}' AND time <= '{tstop_str}'"
        output = self.query(query)


    def format_time_for_InfluxDB(self, time:datetime)->str:
        """Formats a datetime object to the ISO 8601 format required by InfluxDB, ensuring it is in UTC timezone.

        Args:
            time (datetime): The datetime object to format.
        """
        return time.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        

    def get_values_at_times(self,times:pd.Series, measurements:list, )->pd.DataFrame:
        """return a dataframe where each columns is the value of each measurement of the the sensors given in the list 'measurement' from the InfluxDB database. Time is returned as the "Time". If no measruement is found, return nan.

        Parameters
        ----------
        times : pd.Series
            the list of times to which we want the measurement. If not timezone is provided, the default timezone is Santiago'time.
        measurements : list of string
            list of measurement to be queried
       
        Returns
        -------
        pd.DataFrame
            dataframe of size len(times) and len(measurements)+1 columns. Column names are "Time" and the name of each measurement required.
        """
        if isinstance(measurements, str):
            measurements=[measurements]
        
        ## -- Format time --
        # check timezone
        times_original = times
        if isinstance(times,  (np.ndarray, list)):
            times = pd.Series(pd.to_datetime(times))
        if times.dt.tz is None: # check timezone
            times = times.dt.tz_localize(DEFAULT_TZ)
        ## get min and max times
        tmin,tmax=times.min()-timedelta(seconds=10),times.max()+timedelta(seconds=10)
        ## Influx work with UTC --
        tmin, tmax = self.format_time_for_InfluxDB(tmin) ,self.format_time_for_InfluxDB(tmax) 

        ## -- Prepare query -- 
        # query exemple: SELECT "value" FROM "temp_k_phidget", "temp_k_table_laser" WHERE time >= '2026-03-13T13:01:50Z' AND time <= '2026-03-13T13:10:10Z'
        measurement_str =""
        for meas_name in measurements:
            measurement_str +=f"\"{meas_name}\", "
        measurement_str= measurement_str[:-2]
        query = f"SELECT \"value\" FROM {measurement_str} WHERE time >= '{tmin}' AND time <= '{tmax}'"
        query_output = self.query(query)

        ## -- Prepare the outptut ---
        # We will return output to the user. It is a dataframe which contains the original time list and all the measurement
        output = pd.DataFrame({"Time":times_original, "time UTC":times.dt.tz_convert(timezone.utc)})
        liste_finale = []

        for (meas_name, tags), points in query_output.items():
            # -- df is a dataframe with two columns, one is time UTC and the other is {meas_name}
            df = pd.DataFrame(points).rename(columns={"time":"time UTC", "value":meas_name})    
            df["time UTC"] = pd.to_datetime(df['time UTC'], utc=True).astype(output["time UTC"].dtype)
            output = pd.merge_asof(output,df, on= "time UTC" )
        # Now we fill of NaN where no data where get
        for meas_name in measurements:
            if not meas_name in output.keys():
                log.warning(f"No data found on {meas_name} in the time range provided [{tmin}, {tmax}]")
                output[meas_name]= np.full(len(output), fill_value = np.nan)
        # return the dataframe with len(measurements) + 1 columns
        return output[["Time"]+measurements]
    
    def write_to_db(self, descr, unit, measurement,location, category, sensor_type, save_raw=False, raw=None, force_write=False):
        """Write measurement result to InfluxDB database. 
        force_write: bool, optional,
            If True, we do not use the buffer.
        """
        json_dict = {}
        json_dict["measurement"] = descr
        json_dict["tags"] = {}
        json_dict["tags"]["unit"] = unit
        json_dict["tags"]["location"] = location
        json_dict["tags"]["category"] = category
        json_dict["tags"]["sensor_type"] = sensor_type
        # Grafana assumes UTC:
        json_dict["time"] = datetime.utcnow().strftime("%m/%d/%Y %H:%M:%S")
        json_dict["fields"] = {}
        json_dict["fields"]["value"] = measurement
        if save_raw:
            json_dict["fields"]["raw"] = raw

        if not self.use_buffer:
            self.write_points([json_dict])
        elif force_write:
            self.write_points([json_dict])
        else:
            self.add_to_buffer(db_point=json_dict)

    def add_to_buffer(self, db_point):
        """Adds a point to the buffer. If buffer is full, write points to database and empty the buffer.

        Parameters
        ----------
        db_point : dic
            point to send to the influx database.
        """
        self.buffer.append(db_point)
        if len(self.buffer) >= self.buffer_size:
            log.debug("[Database] Size of buffer is {}. Sending all points to the database.".format(len(self.buffer)))
            self.write_points(self.buffer)
            self.buffer=[]

    def get_measurements_list(self):
        res = self.get_list_measurements()
        return [dic["name"] for dic in res]


if __name__ == "__main__":
    client = ExpMonClient()
    if True:
        print(client.get_measurements_list())

    if True:
        start_time = datetime(2026, 3, 13, 10, 2)
        dates_cibles = [start_time + timedelta(minutes=i) for i in range(9)]
        df = client.get_values_at_times(dates_cibles, ["relative_temp_rb_cell"],)
        print(df)
    if False:
        for i in range(10):
            client.write_to_db(descr="test_sensor",
                        unit="V", 
                        measurement=i,
                        location="Somewhere in the Lab",
                        category= "voltage", 
                        sensor_type="voltmeter")
            time.sleep(12)
    if True:
        client.delete_measurement("test_sensor")

