# aramis-to-cte-excel-converter
This software is used for measurements from ARAMIS Differencial Image Correlation (DIC) for calculation of the the thermal expansion coefficient (CTE).

To do so you need to know a lot about the data structure which will be explained in a later commit. If you do not get things running, you can find the results within the folder `./demo_results` where you can find CTE values of three different methods of calculation.

***Important***: The key differenz by methods is the effect of calculating means at multiple places in the process of converting measurments into results. By getting means you lose information! The **Absolut CTE** Methode is focused to use mean as less as possible.  

Currently it is simple the submission for a master thesis.

# Installation
```
python3 -m pip install pandas numpy matplotlib rich alive_progress openpyxl warnings
```
[**Troubleshooting:** Helpful Tips (click here ...)](#troubleshooting)

# Running
```
python3 getCTExcel.py 
```

![MacDown Screenshot](./howtostart.png)

finally it results in:
![MacDown Screenshot](./finalImage.png)

and some Excel Files in the current folder

# Results
From the Excelfiles one can make plots. In my case I used Origin Pro. Each Excelfile has multiple cols but three important (CTE, diffCTE, InterStageCTE):


![MacDown Screenshot](./CTEAbolut.png)



![MacDown Screenshot](./CTEdiff.png)



![MacDown Screenshot](./CTEinterStage.png)



**The given measurments in the /tests folder are transit liquit phase (TLP) foils from 30 µm Ag and 5 µm In and 5 µm Sn !!!**

(... means they are not linear on the hotplate... this was the reason for doing my research about the methods to measure it the right way)

## Inter Stage CTE
![MacDown Screenshot](./kupferinterstagecte.png)
## Differencial CTE
![MacDown Screenshot](./kupferdiffcte.png)
## CTE over the hole length of the probe
![MacDown Screenshot](./kupferreferenzmessung.png)

# <a name="troubleshooting"></a> Troubleshooting
* Windows-Version of the package alive_progress has to be installed with a different name which simple differs by the _ and - in name (alive_progress => alive-progress install)
* sometimes `pip install --upgrade pip` helps
* `pip install rich --upgrade` should fix the rich error under Windows
* Use Mac OS because this is the platform is used for development
* force python letting stdout to be unbuffered using the `-u` flag
* fix alive_progress problems with `pip install alive-progress`
`