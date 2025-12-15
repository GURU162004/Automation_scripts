#Automation Scripts

Scripts written for the automation of following tasks:

1. PostgreSQL Installation 
   
   Intallation of PostgreSQL can be done via git and source zip. Run the installation script of your choice.

2. TPC-H Data Analysis

   Install and Generate the tpch dataset 
   Load the tpch dataset onto the PostgreSQL database.
   Run the tpch queries on Postgres server
   Analyse the execution time of each queries and store the results on a csv file

3. Replication
   
   Setup Master Slave Replication setup on same machine or on two PCs of your choice.
   Setup one Master and Multiple Slaves of your choice
   Monitor the Master and Slave server continuosly
   Failover scenarios implemented:
        If Master fails and Slave is running. The script autmatically promotes the slave to Master
        If Slave fails, a new Slave is created.

4. ClickHouse Extension

   Test the performance of the TPC-H dataset by running the tpch queries on postgres with the pg_clickhouse extension