# -*- coding: utf-8 -*-
"""
Created on Sat Aug  3 14:11:51 2019

@author: Dominic
"""

from math import exp, log, sqrt

from ...finutils.FinCalendar import FinCalendarTypes
from ...finutils.FinCalendar import FinDayAdjustTypes, FinDateGenRuleTypes
from ...finutils.FinDayCount import FinDayCount, FinDayCountTypes
from ...finutils.FinFrequency import FinFrequencyTypes
from ...finutils.FinGlobalVariables import gDaysInYear
from ...finutils.FinMath import ONE_MILLION, INVROOT2PI, N
from ...finutils.FinError import FinError
from ...market.curves.FinCDSCurve import FinCDSCurve
from .FinCDS import FinCDS

RPV01_INDEX = 1  # 0 is FULL, 1 is CLEAN

###############################################################################


class FinCDSIndexOption(object):

    ''' Class to manage the pricing and risk management of an option to enter
    into a CDS index. Different pricing algorithms are presented.'''

    def __init__(self,
                 expiryDate,
                 maturityDate,
                 indexCoupon,
                 strikeCoupon,
                 notional=ONE_MILLION,
                 longProtection=True,
                 frequencyType=FinFrequencyTypes.QUARTERLY,
                 dayCountType=FinDayCountTypes.ACT_360,
                 calendarType=FinCalendarTypes.WEEKEND,
                 busDayAdjustType=FinDayAdjustTypes.FOLLOWING,
                 dateGenRuleType=FinDateGenRuleTypes.BACKWARD):
        ''' Initialisation of the class object. Note that a large number of the
        inputs are set to default values in line with the standard contract.'''

        if expiryDate > maturityDate:
            raise FinError("Expiry date after end date")

        if indexCoupon < 0.0:
            raise FinError("Index coupon is negative")

        if strikeCoupon < 0.0:
            raise FinError("Index Option strike coupon is negative")

        if dayCountType not in FinDayCountTypes:
            raise FinError(
                "Unknown Fixed Day Count Rule type " +
                str(dayCountType))

        if frequencyType not in FinFrequencyTypes:
            raise FinError(
                "Unknown Fixed Frequency type " +
                str(frequencyType))

        if calendarType not in FinCalendarTypes:
            raise FinError("Unknown Calendar type " + str(calendarType))

        if busDayAdjustType not in FinDayAdjustTypes:
            raise FinError(
                "Unknown Business Day Adjust type " +
                str(busDayAdjustType))

        if dateGenRuleType not in FinDateGenRuleTypes:
            raise FinError(
                "Unknown Date Gen Rule type " +
                str(dateGenRuleType))

        self._expiryDate = expiryDate
        self._maturityDate = maturityDate
        self._indexCoupon = indexCoupon
        self._strikeCoupon = strikeCoupon
        self._notional = notional
        self._longProtection = longProtection

        self._dayCountType = dayCountType
        self._dateGenRuleType = dateGenRuleType
        self._calendarType = calendarType
        self._frequencyType = frequencyType
        self._businessDateAdjustType = busDayAdjustType

        self._cdsContract = FinCDS(self._expiryDate,
                                   self._maturityDate,
                                   self._indexCoupon,
                                   1.0,
                                   self._longProtection,
                                   self._frequencyType,
                                   self._dayCountType,
                                   self._calendarType,
                                   self._businessDateAdjustType,
                                   self._dateGenRuleType)

###############################################################################

    def valueAdjustedBlack(self,
                           valuationDate,
                           indexCurve,
                           indexRecovery,
                           liborCurve,
                           sigma):
        ''' This approach uses two adjustments to Black's option pricing
        model to value an option on a CDS index. '''

        k = self._strikeCoupon
        c = self._indexCoupon
        timeToExpiry = (self._expiryDate - valuationDate) / gDaysInYear
        df = liborCurve.df(timeToExpiry)
        qExpiryIndex = indexCurve.survProb(timeToExpiry)

        cds = FinCDS(valuationDate, self._maturityDate, k)
        strikeCurve = FinCDSCurve(
            valuationDate, [cds], liborCurve, indexRecovery)
#        qExpiryStrike = strikeCurve.survivalProbability(timeToExpiry)

        strikeRPV01 = self._cdsContract.riskyPV01(
            valuationDate, strikeCurve)[RPV01_INDEX]
        indexRPV01 = self._cdsContract.riskyPV01(
            valuationDate, indexCurve)[RPV01_INDEX]

        s = self._cdsContract.parSpread(valuationDate, indexCurve)

        fep = df * (1.0 - qExpiryIndex) * (1.0 - indexRecovery)
        adjFwd = s + fep / indexRPV01
        adjStrike = c + (k - c) * strikeRPV01 / indexRPV01 / qExpiryIndex

        denom = sigma * sqrt(timeToExpiry)
        d1 = log(adjFwd / adjStrike) + 0.5 * sigma * sigma * timeToExpiry
        d2 = log(adjFwd / adjStrike) - 0.5 * sigma * sigma * timeToExpiry
        d1 /= denom
        d2 /= denom

        v_pay = (adjFwd * N(d1) - adjStrike * N(d2)) * indexRPV01
        v_rec = (adjStrike * N(-d2) - adjFwd * N(-d1)) * indexRPV01

        v_pay *= self._notional
        v_rec *= self._notional

        return (v_pay, v_rec)

###############################################################################

    def valueAnderson(self,
                      valuationDate,
                      issuerCurves,
                      indexRecovery,
                      sigma):
        ''' This function values a CDS index option following approach by
        Anderson (2006). This ensures that the no-arbitrage relationship between
        the consituent CDS contract and the CDS index is enforced. It models
        the forward spread as a log-normally distributed quantity and uses the
        credit triangle to compute the forward RPV01. '''

        numCredits = len(issuerCurves)
        timeToExpiry = (self._expiryDate - valuationDate) / gDaysInYear
#        timeToMaturity = (self._maturityDate - valuationDate) / gDaysInYear
        dfToExpiry = issuerCurves[0].df(timeToExpiry)
        liborCurve = issuerCurves[0]._liborCurve

        k = self._strikeCoupon
        c = self._indexCoupon

        strikeCDS = FinCDS(
            self._expiryDate,
            self._maturityDate,
            self._strikeCoupon,
            1.0)
        strikeCurve = FinCDSCurve(valuationDate, [strikeCDS], liborCurve)
        strikeRPV01s = strikeCDS.riskyPV01(valuationDate, strikeCurve)
        qToExpiry = strikeCurve.survProb(timeToExpiry)
        strikeValue = (k - c) * strikeRPV01s[RPV01_INDEX]
        strikeValue /= (dfToExpiry * qToExpiry)

        expH = 0.0
        h1 = 0.0
        h2 = 0.0

        for iCredit in range(0, numCredits):

            issuerCurve = issuerCurves[iCredit]
            q = issuerCurve.survProb(timeToExpiry)
            dh1 = (1.0 - issuerCurve._recoveryRate) * (1.0 - q)

            s = self._cdsContract.parSpread(valuationDate, issuerCurve)
            rpv01 = self._cdsContract.riskyPV01(valuationDate, issuerCurve)
            dh2 = (s - c) * rpv01[RPV01_INDEX] / (dfToExpiry * qToExpiry)

            h1 = h1 + dh1
            h2 = h2 + dh2

        expH = (h1 + h2) / numCredits

        x = self.solveForX(valuationDate,
                           sigma,
                           c,
                           indexRecovery,
                           liborCurve,
                           expH)

        v = self.calcIndexPayerOptionPrice(valuationDate,
                                           x,
                                           sigma,
                                           c,
                                           strikeValue,
                                           liborCurve,
                                           indexRecovery)

        v = v[1]
        v_pay = v * self._notional
        v_rec = v_pay + (strikeValue - expH) * dfToExpiry * self._notional
        strikeValue *= 10000.0
        x *= 10000.0
        expH *= 10000.0
        return v_pay, v_rec, strikeValue, x, expH

###############################################################################

    def solveForX(self,
                  valuationDate,
                  sigma,
                  indexCoupon,
                  indexRecovery,
                  liborCurve,
                  expH):
        ''' Function to solve for the arbitrage free '''
        x1 = 0.0
        x2 = 0.9999
        ftol = 1e-8
        jmax = 40
        xacc = 0.000000001
        rtb = 999999

        f = self.calcObjFunc(x1, valuationDate, sigma, indexCoupon,
                             indexRecovery, liborCurve) - expH

        fmid = self.calcObjFunc(x2, valuationDate, sigma, indexCoupon,
                                indexRecovery, liborCurve) - expH

        if f * fmid >= 0.0:
            raise FinError("Solution not bracketed.")

        if f < 0.0:
            rtb = x1
            dx = x2 - x1
        else:
            rtb = x2
            dx = x1 - x2

        for j in range(0, jmax):
            dx = dx * 0.5
            xmid = rtb + dx
            fmid = self.calcObjFunc(xmid, valuationDate, sigma, indexCoupon,
                                    indexRecovery, liborCurve) - expH
            if fmid <= 0.0:
                rtb = xmid
            if abs(dx) < xacc or abs(fmid) < ftol:
                return rtb

        return rtb

###############################################################################

    def calcObjFunc(self,
                    x,
                    valuationDate,
                    sigma,
                    indexCoupon,
                    indexRecovery,
                    liborCurve):
        ''' An internal function used in the Anderson valuation. '''

        # The strike value is not relevant here as we want the zeroth element
        # of the return value
        strikeValue = 0.0

        values = self.calcIndexPayerOptionPrice(valuationDate,
                                                x,
                                                sigma,
                                                self._indexCoupon,
                                                strikeValue,
                                                liborCurve,
                                                indexRecovery)

        return values[0]

###############################################################################

    def calcIndexPayerOptionPrice(self,
                                  valuationDate,
                                  x,
                                  sigma,
                                  indexCoupon,
                                  strikeValue,
                                  liborCurve,
                                  indexRecovery):
        ''' Calculates the intrinsic value of the index payer swap and the
        value of the index payer option which are both returned in an array. '''

        z = -6.0
        dz = 0.2
        numZSteps = int(2.0 * abs(z) / dz)

        flowDates = self._cdsContract._adjustedDates
        numFlows = len(flowDates)
        texp = (self._expiryDate - valuationDate) / gDaysInYear
        dfToExpiry = liborCurve.df(texp)
        lgd = 1.0 - indexRecovery

        fwdDfs = [1.0] * (numFlows)
        expiryToFlowTimes = [1.0] * (numFlows)

        for iFlow in range(1, numFlows):
            expiryToFlowTimes[iFlow] = (
                flowDates[iFlow] - self._expiryDate) / gDaysInYear
            fwdDfs[iFlow] = liborCurve.df(flowDates[iFlow]) / dfToExpiry

        intH = 0.0
        intMaxH = 0.0

        dayCount = FinDayCount(self._dayCountType)
        pcd = flowDates[0]  # PCD
        eff = self._expiryDate
        accrualFactorPCDToExpiry = dayCount.yearFrac(pcd, eff)

        s0 = exp(-0.5 * sigma * sigma * texp)

        for iStep in range(0, numZSteps):
            s = x * s0 * exp(sigma * sqrt(texp) * z)
            pdf = exp(-(z**2) / 2.0)
            z = z + dz

            fwdRPV01 = 0.0
            for iFlow in range(1, numFlows):
                accFactor = self._cdsContract._accrualFactors[iFlow]
                survivalProbability = exp(-s * expiryToFlowTimes[iFlow] / lgd)
                fwdRPV01 += accFactor * survivalProbability * fwdDfs[iFlow]

            fwdRPV01 += -accrualFactorPCDToExpiry
            h = (s - indexCoupon) * fwdRPV01
            maxh = max(h - strikeValue, 0.0)

            intH += h * pdf
            intMaxH += maxh * pdf

        intH *= INVROOT2PI * dz
        intMaxH *= INVROOT2PI * dz * dfToExpiry
        return intH, intMaxH

###############################################################################
