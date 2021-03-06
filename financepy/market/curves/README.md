# Curves
## Overview
These modules create a family of curve types related to the term structures of interest rates. There are two basic types of curve:

1. Best fit yield curves fitting to bond prices which are used for interpolation. A range of curve shapes from polynomials to B-Splines is available.
2. Discount curves that can be used to present value a future cash flow. These differ from best fits curves in that they exactly refit the prices of bonds or CDS. The different discount curves are created by calibrating to different instruments. They also differ in terms of the term structure shapes they can have. Different shapes have different impacts in terms of locality on risk management performed using these different curves. There is often a trade-off between smoothness and locality.

## Best Fit Bond Curves
The first category are FinBondYieldCurves.

### FinBondYieldCurve
This module describes a curve that is fitted to bond yields calculated from bond market prices supplied by the user. The curve is not guaranteed to fit all of the bond prices exactly and a least squares approach is used. A number of fitting forms are provided which consist of 

* Polynomial 
* Nelson-Siegel
* Nelson-Siegal-Svensson
* Cubic B-Splines

This fitted curve cannot be used for pricing as yields assume a flat term structure. It can be used for fitting and interpolating yields off a nicely constructed yield curve interpolation curve.

### FinCurveFitMethod
This module sets out a range of curve forms that can be fitted to the bond yields. These includes a number of parametric curves that can be used to fit yield curves. These include:
* Polynomials of any degree 
* Nelson-Siegel functional form. 
* Nelson-Siegel-Svensson functional form.
* B-Splines

### FinNelsonSiegelCurve
Implementation of the Nelson-Siegel and the Nelson-Siegel-Svensson curves.

## Discount Curves
These are curves that can be used to discount cashflows.

### FinDiscountCurve
This is a class that holds a Numpy array of times and discount factor values that represents a discount curve. It also requires a specific interpolation scheme. A function is also provided to return a survival probability so that this class can also be used to handle term structures of survival probabilities.

### FinBondZeroCurve
This is a discount curve that is extracted by bootstrapping a zero rate curve such that it exactly reprices the set of bonds provided. The internal representation of the curve are discount factors on each of the bond maturity dates. Between these dates, discount factors are interpolated according to a specified scheme - see below.

### FinLiborCurve
This is a discount curve that is extracted by bootstrapping a set of Libor deposits, Libor FRAs and Libor swap prices. The internal representation of the curve are discount factors on each of the deposit, FRA and swap maturity dates. Between these dates, discount factors are interpolated according to a specified scheme - see below.

### FinCDSCurve
This is a curve that has been calibrated to fit the market term structure of CDS contracts given a recovery rate assumption and a FinLiborCurve discount curve. It also contains a LiborCurve object for discounting. It has methods for fitting the curve and also for extracting survival probabilities.

### FinInterpolate
This module contains the interpolation function used throughout the discount curves when a discount factor needs to be interpolated. There are three interpolation methods:

1. PIECEWISE LINEAR - This assumes that a discount factor at a time between two other known discount factors is obtained by linear interpolation. This approach does not guarantee any smoothness but is local. It does not guarantee positive forwards (assuming positive zero rates).
2. PIECEWISE LOG LINEAR - This assumes that the log of the discount factor is interpolated linearly. The log of a discount factor to time T is T x R(T) where R(T) is the zero rate. So this is not linear interpolation of R(T) but of T x R(T).
3. FLAT FORWARDS - This interpolation assumes that the forward rate is constant between discount factor points. It is not smooth but is highly local and also ensures positive forward rates if the zero rates are positive.
