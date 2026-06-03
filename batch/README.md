# Batch Processing — Apache Spark

This folder contains two PySpark notebooks that demonstrate distributed data processing on NYC taxi trip data. 
Spark runs locally in a WSL environment with Java 17, isolated from the Windows host to avoid runtime conflicts with other Java versions.


## Notes

- Requires Java 17 and Apache Spark 4.x installed in WSL.
- Spark output files are excluded from git via `.gitignore`.