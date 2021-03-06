#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
import sys

import datetime as dt
from dateutil.relativedelta import relativedelta

# Benchmark entry for D3, added after the competition deadline. The entry simply uses the last known value.
# Based on an MATLAB script by Daniel Alexander and Neil Oxtoby.
# ============
# Authors:
#   Razvan Valentin-Marinescu




## Read in the TADPOLE data set and extract a few columns of salient information.
# Script requires that TADPOLE_D1_D2.csv is in the parent directory. Change if
# necessary
dataLocation = '../'  # parent directory

tadpoleD1D2File = os.path.join(dataLocation, 'TADPOLE_D1_D2.csv')
tadpoleD3File = os.path.join(dataLocation, 'TADPOLE_D3.csv')
outputFile = 'TADPOLE_Submission_BenchmarkLastVisit-ID-5.csv' # set ID 5, so that it is recognised as a D3 prediction



errorFlag = 0
if not os.path.exists(tadpoleD1D2File):
  print('File {0} does not exist! \nYou need to download it from ADNI\n and/or move it in the right directory'.format(
    tadpoleD1D2File))
  errorFlag = 1
if not os.path.exists(tadpoleD3File):
  print('File {0} does not exist! \nYou need to download it from ADNI\n and/or move it in the right directory'.format(
    tadpoleD3File))
  errorFlag = 1

if errorFlag:
  sys.exit()

# choose whether to display warning messages
verbose = 0

# * Read in the D1_D2 spreadsheet: may give a DtypeWarning, but the read/import works.
# * This file contains all the necessary data - the TADPOLE_LB1_LB2.csv spreadsheet contains
# * only the LB1 and LB2 indicators, aligned to TADPOLE_D1_D2.csv
tableD2 = pd.read_csv(tadpoleD1D2File, low_memory=False)
tableD2 = tableD2[tableD2.D2 == 0]

tableD3 = pd.read_csv(tadpoleD3File, low_memory=False)


# * Target variables: convert strings to numeric if necessary
variablesToCheck = ['RID', 'ICV_bl', 'DX', 'ADAS13', 'Ventricles']
for kt in range(0, len(variablesToCheck)):
  # print(tableD2.loc[:,variablesToCheck[kt]])
  var0 = tableD2.loc[:, variablesToCheck[kt]].values[0]
  if not ('DX' == variablesToCheck[kt]):
    if np.str(var0) == var0:
      # * Convert strings to numeric
      tableD2[variablesToCheck[kt]] = np.int(tableD2[variablesToCheck[kt]])

variablesToCheck = ['RID', 'ICV', 'DX', 'ADAS13', 'Ventricles']
for kt in range(0, len(variablesToCheck)):
  var0 = tableD3.loc[:,variablesToCheck[kt]].values[0]
  if not ('DX' == variablesToCheck[kt]):
    if np.str(var0) == var0:
      # * Convert strings to numeric
      tableD3[variablesToCheck[kt]] = np.int(tableD3[variablesToCheck[kt]])


# * Copy numeric target variables into arrays. Missing data is encoded as -1
# ADAS13 scores
ADAS13_Col = np.concatenate((tableD2.ADAS13.values.copy(), tableD3.ADAS13.values.copy()))
Ventricles_Col = np.concatenate((tableD2.Ventricles.values.copy(), tableD3.Ventricles.values.copy()))
ICV_Col = np.concatenate((tableD2.ICV_bl.values.copy(), tableD3.ICV.values.copy()))
DXCHANGE = np.concatenate((tableD2.DX.values.copy(), tableD3.DX.values.copy()))  # 'NL to MCI', 'MCI to Dementia', etc.
DX = DXCHANGE.copy() # Note: missing data encoded numerically (!) as nan
RID_Col = np.concatenate((tableD2.RID.values.copy(), tableD3.RID.values.copy()))
EXAMDATE = np.concatenate((tableD2.EXAMDATE.values.copy(), tableD3.EXAMDATE.values.copy()))


# * Copy the column specifying membership of LB2 into an array.
D3_col = np.concatenate((np.zeros(tableD2.EXAMDATE.values.shape[0]), np.ones(tableD3.EXAMDATE.values.shape[0])))

assert ADAS13_Col.shape[0] == Ventricles_Col.shape[0]
assert ADAS13_Col.shape[0] == ICV_Col.shape[0]
assert ADAS13_Col.shape[0] == DXCHANGE.shape[0]
assert ADAS13_Col.shape[0] == DX.shape[0]
assert ADAS13_Col.shape[0] == RID_Col.shape[0]
assert ADAS13_Col.shape[0] == EXAMDATE.shape[0]
assert ADAS13_Col.shape[0] == D3_col.shape[0]



ADAS13_Col[np.isnan(ADAS13_Col)] = -1
# Ventricles volumes, normalised by intracranial volume
Ventricles_Col[np.isnan(Ventricles_Col)] = -1
ICV_Col[np.isnan(ICV_Col)] = -1
ICV_Col[Ventricles_Col == -1] = 1
Ventricles_ICV_Col = Ventricles_Col / ICV_Col
# * Create an array containing the clinical status column from the spreadsheet
# DXCHANGE: current diagnosis (DX) and change since most recent visit, i.e., '[previous DX] to [current DX]'

# Convert DXCHANGE to current DX
for kr in range(0, len(DX)):
  if np.isreal(DX[kr]):  # Missing data
    DX[kr] = ''  # missing data encoded as empty string
  else:
    # Loop until finding the final space in the DXCHANGE string
    idxn = 0  # reset
    while not (idxn == -1):
      idx = idxn
      idxn = DX[kr].find(' ', idxn + 1)
    if idx > 0:
      idx = idx + 1
    DX[kr] = DX[kr][idx:]  # extract current DX from DXCHANGE
CLIN_STAT_Col = DX.copy()

# * Copy the subject ID column from the spreadsheet into an array.

RID_Col[np.isnan(RID_Col)] = -1  # missing data encoded as -1

# * Compute months since Jan 2000 for each exam date
ref = dt.datetime(2000, 1, 1)

ExamMonth_Col = np.zeros(len(EXAMDATE))
for k in range(0, len(EXAMDATE)):
  d = dt.datetime.strptime(EXAMDATE[k], '%Y-%m-%d') - ref
  ExamMonth_Col[k] = d.days / 365 * 12




## Generate the very simple forecast
print('Generating forecast ...')

# * Get the list of subjects to forecast from LB2 - the ordering is the
# * same as in the submission template.
d2Inds = np.where(D3_col)[0]
D2_SubjList = np.unique(RID_Col[d2Inds])
N_D2 = len(D2_SubjList)

# As opposed to the actual submission, we require 84 months of forecast
# data. This is because some ADNI2 subjects in LB4 have visits as long as
# 7 years after their last ADNI1 visit in LB2

# * Create arrays to contain the 84 monthly forecasts for each LB2 subject
nForecasts = 5 * 12  # forecast 7 years (84 months).
# 1. Clinical status forecasts
#    i.e. relative likelihood of NL, MCI, and Dementia (3 numbers)
CLIN_STAT_forecast = np.zeros([N_D2, nForecasts, 3])
# 2. ADAS13 forecasts
#    (best guess, upper and lower bounds on 50% confidence interval)
ADAS13_forecast = np.zeros([N_D2, nForecasts, 3])
# 3. Ventricles volume forecasts
#    (best guess, upper and lower bounds on 50% confidence interval)
Ventricles_ICV_forecast = np.zeros([N_D2, nForecasts, 3])

# * Our example forecast for each subject is based on the most recent
# * available (not missing) data for each target variable in LB2.

# * Extract most recent data.
# Initialise storage arrays
most_recent_CLIN_STAT = N_D2 * ['']
most_recent_ADAS13 = -1 * np.ones([N_D2, 1])
most_recent_Ventricles_ICV = -1 * np.zeros([N_D2, 1])

display_info = 0  # Useful for checking and debugging (see below)

# *** Defaults - in case of missing data
# * Ventricles
# Missing data = typical volume +/- broad interval = 25000 +/- 20000
Ventricles_typical = 25000
Ventricles_broad_50pcMargin = 20000  # +/- (broad 50% confidence interval)
# Default CI = 1000
Ventricles_default_50pcMargin = 1000  # +/- (broad 50% confidence interval)
# Convert to Ventricles/ICV via linear regression
nm = np.all(np.stack([Ventricles_Col > 0, ICV_Col > 0]), 0)  # not missing: Ventricles and ICV
x = Ventricles_Col[nm]
y = Ventricles_ICV_Col[nm]
lm = np.polyfit(x, y, 1)
p = np.poly1d(lm)

Ventricles_ICV_typical = p(Ventricles_typical)
Ventricles_ICV_broad_50pcMargin = np.abs(p(Ventricles_broad_50pcMargin) - p(-Ventricles_broad_50pcMargin)) / 2
Ventricles_ICV_default_50pcMargin = np.abs(p(Ventricles_default_50pcMargin) - p(-Ventricles_default_50pcMargin)) / 2
# * ADAS13
ADAS13_typical = 12
ADAS13_typical_lower = ADAS13_typical - 10
ADAS13_typical_upper = ADAS13_typical + 10

for i in range(0, N_D2):  # Each subject in LB2
  # * Rows in LB2 corresponding to Subject LB2_SubjList(i)
  subj_rows = np.where(np.all(np.stack([RID_Col == D2_SubjList[i], D3_col], 0), 0))[0]
  subj_exam_dates = ExamMonth_Col[subj_rows]
  # Non-empty data among these rows
  exams_with_CLIN_STAT = CLIN_STAT_Col[subj_rows] != ''
  exams_with_ADAS13 = ADAS13_Col[subj_rows] > 0
  exams_with_ventsv = Ventricles_ICV_Col[subj_rows] > 0
  # exams_with_allData   = exams_with_CLIN_STAT & exams_with_ADAS13 & exams_with_ventsv

  # * Extract most recent non-empty data
  # 1. Clinical status
  if sum(exams_with_CLIN_STAT) >= 1:  # Subject has a Clinical status
    # Index of most recent visit with a Clinical status
    ind = subj_rows[
      np.all(np.stack([subj_exam_dates == max(subj_exam_dates[exams_with_CLIN_STAT]), exams_with_CLIN_STAT], 0), 0)]
    most_recent_CLIN_STAT[i] = CLIN_STAT_Col[ind[-1]]
  else:  # Subject has no Clinical statuses in the data set
    most_recent_CLIN_STAT[i] = ''  # Already set when initialised above

  # 2. ADAS13 score
  if sum(exams_with_ADAS13) >= 1:  # Subject has an ADAS13 score
    # Index of most recent visit with an ADAS13 score
    ind = subj_rows[
      np.all(np.stack([subj_exam_dates == max(subj_exam_dates[exams_with_ADAS13]), exams_with_ADAS13], 0), 0)]
    most_recent_ADAS13[i] = ADAS13_Col[ind[-1]]
  else:  # Subject has no ADAS13 scores in the data set
    most_recent_ADAS13[i] = -1  # Already set when initialised above
  # 3. Most recent ventricles volume measurement
  if sum(exams_with_ventsv) >= 1:  # Subject has a ventricles volume recorded
    # Index of most recent visit with a ventricles volume
    ind = subj_rows[
      np.all(np.stack([subj_exam_dates == max(subj_exam_dates[exams_with_ventsv]), exams_with_ventsv], 0), 0)]
    most_recent_Ventricles_ICV[i] = Ventricles_ICV_Col[ind[-1]]
  else:  # Subject has no ventricle volume measurement in the data set
    most_recent_Ventricles_ICV[i] = -1  # Already set when initialised above

  # * "Debug mode": prints out some stuff (set display_info=1 above)
  if display_info:
    print('{0} - CLIN_STAT {1} - ADAS13 {2} - Ventricles_ICV {3}'.format(i, most_recent_CLIN_STAT[i], most_recent_ADAS13[i],
                                                                     most_recent_Ventricles_ICV[i]))

  # *** Construct example forecasts
  # * Clinical status forecast: predefined likelihoods per current status
  if most_recent_CLIN_STAT[i] == 'NL':
    CNp, MCIp, ADp = [1, 0, 0]
  elif most_recent_CLIN_STAT[i] == 'MCI':
    CNp, MCIp, ADp = [0, 1, 0]
  elif most_recent_CLIN_STAT[i] == 'Dementia':
    CNp, MCIp, ADp = [0, 0, 1]
  else:
    CNp, MCIp, ADp = [0.33, 0.33, 0.34]
    if verbose:
      print('Unrecognised status ' + most_recent_CLIN_STAT[i])
  # Use the same clinical status probabilities for all months
  CLIN_STAT_forecast[i, :, 0] = CNp
  CLIN_STAT_forecast[i, :, 1] = MCIp
  CLIN_STAT_forecast[i, :, 2] = ADp
  # * ADAS13 forecast: = most recent score, default confidence interval
  if most_recent_ADAS13[i] >= 0:
    ADAS13_forecast[i, :, 0] = most_recent_ADAS13[i]
    ADAS13_forecast[i, :, 1] = max([0, most_recent_ADAS13[i] - 1])  # Set to zero if best-guess less than 1.
    ADAS13_forecast[i, :, 2] = most_recent_ADAS13[i] + 1
  else:
    # Subject has no history of ADAS13 measurement, so we'll take a
    # typical score of 12 with wide confidence interval +/-10.
    ADAS13_forecast[i, :, 0] = ADAS13_typical
    ADAS13_forecast[i, :, 1] = ADAS13_typical_lower
    ADAS13_forecast[i, :, 2] = ADAS13_typical_upper
  # * Ventricles volume forecast: = most recent measurement, default confidence interval
  if most_recent_Ventricles_ICV[i] > 0:
    Ventricles_ICV_forecast[i, :, 0] = most_recent_Ventricles_ICV[i]
    Ventricles_ICV_forecast[i, :, 1] = most_recent_Ventricles_ICV[i] - Ventricles_ICV_default_50pcMargin
    Ventricles_ICV_forecast[i, :, 2] = most_recent_Ventricles_ICV[i] + Ventricles_ICV_default_50pcMargin
  else:
    # Subject has no imaging history, so we'll take a typical
    # ventricles volume of 25000 & wide confidence interval +/-20000
    Ventricles_ICV_forecast[i, :, 0] = Ventricles_ICV_typical
    Ventricles_ICV_forecast[i, :, 1] = Ventricles_ICV_typical - Ventricles_ICV_broad_50pcMargin
    Ventricles_ICV_forecast[i, :, 2] = Ventricles_ICV_typical + Ventricles_ICV_broad_50pcMargin

Ventricles_ICV_forecast = np.around(1e9 * Ventricles_ICV_forecast,
                                    0) / 1e9  # round to 9 decimal places to match MATLAB equivalent

## Now construct the forecast spreadsheet and output it.
print('Constructing the output spreadsheet {0} ...'.format(outputFile))
submission_table = pd.DataFrame()
# * Repeated matrices - compare with submission template
submission_table['RID'] = D2_SubjList.repeat(nForecasts)
submission_table['ForecastMonth'] = np.tile(range(1, nForecasts + 1), (N_D2, 1)).flatten()
# * Submission dates - compare with submission template
startDate = dt.datetime(2010, 5, 1)
endDate = startDate + relativedelta(months=+nForecasts - 1)
ForecastDates = [startDate]
while ForecastDates[-1] < endDate:
  ForecastDates.append(ForecastDates[-1] + relativedelta(months=+1))
ForecastDatesStrings = [dt.datetime.strftime(d, '%Y-%m') for d in ForecastDates]
submission_table['ForecastDate'] = np.tile(ForecastDatesStrings, (N_D2, 1)).flatten()
# * Pre-fill forecast data, encoding missing data as NaN
nanColumn = np.repeat(np.nan, submission_table.shape[0])
submission_table['CNRelativeProbability'] = nanColumn
submission_table['MCIRelativeProbability'] = nanColumn
submission_table['ADRelativeProbability'] = nanColumn
submission_table['ADAS13'] = nanColumn
submission_table['ADAS1350_CILower'] = nanColumn
submission_table['ADAS1350_CIUpper'] = nanColumn
submission_table['Ventricles_ICV'] = nanColumn
submission_table['Ventricles_ICV50_CILower'] = nanColumn
submission_table['Ventricles_ICV50_CIUpper'] = nanColumn

# *** Paste in month-by-month forecasts **
# * 1. Clinical status
submission_table['CNRelativeProbability'] = CLIN_STAT_forecast[:, :, 0].flatten()
submission_table['MCIRelativeProbability'] = CLIN_STAT_forecast[:, :, 1].flatten()
submission_table['ADRelativeProbability'] = CLIN_STAT_forecast[:, :, 2].flatten()
# * 2. ADAS13 score
submission_table['ADAS13'] = ADAS13_forecast[:, :, 0].flatten()
# Lower and upper bounds (50% confidence intervals)
submission_table['ADAS1350_CILower'] = ADAS13_forecast[:, :, 1].flatten()
submission_table['ADAS1350_CIUpper'] = ADAS13_forecast[:, :, 2].flatten()
# * 3. Ventricles volume (normalised by intracranial volume)
submission_table['Ventricles_ICV'] = Ventricles_ICV_forecast[:, :, 0].flatten()
# Lower and upper bounds (50% confidence intervals)
submission_table['Ventricles_ICV50_CILower'] = Ventricles_ICV_forecast[:, :, 1].flatten()
submission_table['Ventricles_ICV50_CIUpper'] = Ventricles_ICV_forecast[:, :, 2].flatten()

# * Convert all numbers to strings - only useful in MATLAB
# hdr = submission_table.columns.copy()
# for k in range(0,len(hdr)):
#     if np.all(np.isreal(submission_table[hdr[k]].values)):
#         submission_table[hdr[k]] = submission_table[hdr[k]].values.astype(str)

# * Use column names that match the submission template
submission_table.rename(columns={'RID': 'RID',
                                 'ForecastMonth': 'Forecast Month',
                                 'ForecastDate': 'Forecast Date',
                                 'CNRelativeProbability': 'CN relative probability',
                                 'MCIRelativeProbability': 'MCI relative probability',
                                 'ADRelativeProbability': 'AD relative probability',
                                 'ADAS13': 'ADAS13',
                                 'ADAS1350_CILower': 'ADAS13 50% CI lower',
                                 'ADAS1350_CIUpper': 'ADAS13 50% CI upper',
                                 'Ventricles_ICV': 'Ventricles_ICV',
                                 'Ventricles_ICV50_CILower': 'Ventricles_ICV 50% CI lower',
                                 'Ventricles_ICV50_CIUpper': 'Ventricles_ICV 50% CI upper'}, inplace=True)
# * Write to file
submission_table.to_csv(outputFile, index=False)
